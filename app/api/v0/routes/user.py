from datetime import timedelta
from logging import Logger
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi import status as http_status
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from pyfa_converter import FormDepends
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import admin as admin_model
from app.models import auth as auth_model
from app.models import comment as comment_model
from app.models import post as post_model
from app.models import user as user_model
from app.schemas import admin as admin_schema
from app.schemas import auth as auth_schema
from app.schemas import post as post_schema
from app.schemas import user as user_schema
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import basic as basic_utils
from app.utils import email as email_utils
from app.utils import image as image_utils
from app.utils import log as log_utils
from app.utils import map as map_utils
from app.utils import password as password_utils

router = APIRouter(prefix=settings.api_prefix + "/users", tags=["Users"])

MAX_SIZE = settings.image_max_size

image_folder = settings.image_folder


# create new user
@router.post("/register", status_code=http_status.HTTP_201_CREATED)
def create_user(
    background_tasks: BackgroundTasks,
    request: user_schema.UserRegister = FormDepends(user_schema.UserRegister),  # type: ignore
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    image: UploadFile | None = None,
):
    # check if user registered but unverified
    unverified_user = user_service.get_user_by_email(
        email=request.email,
        status_not_in_list=[
            "ACT",
            "DAH",
            "RSF",
            "RSP",
            "TBN",
            "PDH",
            "PBN",
            "PDI",
            "PDB",
            "DEL",
        ],
        db_session=db,
        is_verified=False,
    )

    if unverified_user:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"{unverified_user.email} is already registered. Verification Pending.",
        )
        # redirect to verification page (front end)

    # check both entered passwords are same
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    del request.confirm_password

    # check if username already exists
    username_check = user_service.check_username_exists(
        username=request.username, db_session=db
    )
    if username_check:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Username {request.username} is already taken",
        )
    user_check = user_service.check_user_exists(email=request.email, db_session=db)
    if user_check:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"{request.email} already exists in the system",
        )

    # hash password
    hashed_password = password_utils.get_hash(password=request.password)
    request.password = hashed_password

    user_repr_id = uuid4()

    add_user = user_model.User(**request.dict(), repr_id=user_repr_id)

    # create a subfolder for user specific uploads, if folder exists get it.
    user_subfolder = image_utils.get_or_create_entity_image_subfolder(
        entity="user", repr_id=str(user_repr_id), logger=logger
    )

    # create a subfolder for profile images, if folder exists get it.
    profile_subfolder = image_utils.get_or_create_entity_profile_image_subfolder(
        entity_subfolder=user_subfolder, logger=logger
    )

    # create a subfolder for profile images, if folder exists get it.
    posts_subfolder = image_utils.get_or_create_user_posts_image_subfolder(
        user_subfolder=user_subfolder, logger=logger
    )

    # create a subfolder for appeal attachments, if folder exists get it.
    appeals_subfolder = image_utils.get_or_create_user_appeals_attachment_subfolder(
        user_subfolder=user_subfolder, logger=logger
    )

    image_path = None
    try:
        if image:
            # image validation and handling
            image_name = image_utils.validate_image_generate_name(
                username=request.username,
                image=image,
                logger=logger,
            )

            add_user.profile_picture = image_name

            image_path = profile_subfolder / image_name

            # write image to target
            image_utils.write_image(
                image=image,
                image_path=image_path,
                logger=logger,
            )

        db.add(add_user)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if image and image_path:
            image_utils.remove_image(path=image_path)
        image_utils.remove_folder(path=user_subfolder)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user",
        ) from exc
    except HTTPException as exc:
        image_utils.remove_folder(path=user_subfolder)
        raise exc
    except Exception as exc:
        logger.error(exc, exc_info=True)
        if image and image_path:
            image_utils.remove_image(path=image_path)
        image_utils.remove_folder(path=user_subfolder)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    db.refresh(add_user)

    # generate a token
    claims = {"sub": add_user.email, "role": add_user.type}
    user_verify_token, user_verify_token_id = auth_utils.create_user_verify_token(
        claims=claims
    )

    # generate verification link
    verify_link = (
        f"https://vpkonnect.in/accounts/signup/verify/?token={user_verify_token}"
    )
    email_subject = "VPKonnect - User Verification - Account Signup"
    email_details = admin_schema.SendEmail(
        template="user_account_signup_verification.html",
        email=[EmailStr(add_user.email)],
        body_info={
            "first_name": add_user.first_name,
            "link": verify_link,
            "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
        },
    )
    try:
        # add the token to userverificationcodetoken table
        add_user_verify_token = auth_model.UserVerificationCodeToken(
            code_token_id=user_verify_token_id,
            type="USV",
            user_id=add_user.id,
        )
        db.add(add_user_verify_token)
        db.commit()

        # send email
        email_utils.send_email(email_subject, email_details, background_tasks)

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing verification email request for user registration",
        ) from exc
    except ConnectionErrors as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending mail",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"User registration verification process - An email has been sent to {add_user.email} for verification."
    }


# send verification mail
@router.post("/send-verify-email")
def send_verification_email_user(
    email_user_request: user_schema.UserSendVerifyEmail,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
):
    # get the user
    user = user_service.get_user_by_email(
        email=email_user_request.email,
        status_not_in_list=["PDI", "PDB", "DEL"],
        db_session=db,
        is_verified=None,
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    email_subject = str()
    email_details = None
    token_id = str()
    return_message = None

    # check the type and accordingly set parameters
    if email_user_request.type == "USV":
        if (
            user.status
            in [
                "ACT",
                "DAH",
                "RSF",
                "RSP",
                "TBN",
                "PDH",
                "PBN",
            ]
            or user.is_verified == True
        ):
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="User is already verified",
            )

        # generate a token
        claims = {"sub": user.email, "role": user.type}
        user_token, token_id = auth_utils.create_user_verify_token(claims=claims)

        # generate verification link
        verify_link = f"https://vpkonnect.in/accounts/signup/verify/?token={user_token}"
        email_subject = "VPKonnect - User Verification - Account Signup"
        email_details = admin_schema.SendEmail(
            template="user_account_signup_verification.html",
            email=[EmailStr(email_user_request.email)],
            body_info={
                "first_name": user.first_name,
                "link": verify_link,
                "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
            },
        )
        return_message = f"User registration verification process - An email has been sent to {user.email} for verification."

    elif email_user_request.type == "PWR":
        if user.status in [
            "TBN",
            "PBN",
        ]:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Unable to process your request at this time. Please contact support for assistance.",
            )

        # generate token
        claims = {"sub": user.email, "role": user.type}
        user_token, token_id = auth_utils.create_reset_token(claims=claims)

        # generate reset link
        reset_link = (
            f"https://vpkonnect.in/accounts/password/change/?token={user_token}"
        )

        email_subject = "VPKonnect - Password Reset Request"
        email_details = admin_schema.SendEmail(
            template="password_reset_email.html",
            email=[EmailStr(user.email)],
            body_info={
                "username": user.username,
                "link": reset_link,
                "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
            },
        )
        return_message = f"An email will be sent to {user.email} if an account is registered under it."

    try:
        # add the token to userverificationcodetoken table
        add_user_token = auth_model.UserVerificationCodeToken(
            code_token_id=token_id,
            type=email_user_request.type,
            user_id=user.id,
        )
        db.add(add_user_token)
        db.commit()

        email_utils.send_email(email_subject, email_details, background_tasks)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing email request",
        ) from exc
    except ConnectionErrors as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending mail",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": return_message}


# verify user
@router.post("/register/verify", response_model=user_schema.UserVerifyResponse)
def verify_user_(
    user_verify_token: str = Form(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
):
    # decode token
    token_claims = auth_utils.verify_user_verify_token(token=user_verify_token)
    user_verify_token_blacklist_check = auth_utils.is_token_blacklisted(
        token=token_claims.token_id
    )
    if user_verify_token_blacklist_check:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="User verification failed, Token invalid/revoked",
        )

    # get the user
    user_query = user_service.get_user_by_email_query(
        email=token_claims.email,
        status_not_in_list=[
            "ACT",
            "DAH",
            "RSF",
            "RSP",
            "TBN",
            "PDH",
            "PBN",
            "DEL",
            "PDI",
            "PDB",
        ],
        db_session=db,
        is_verified=False,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="New user to be verfified and registered not found",
        )

    # get the query to fetch all user verify token ids related to the user
    user_verify_token_ids_query = auth_service.get_user_verification_codes_tokens_query(
        user_id=str(user.id), _type="USV", db_session=db
    )

    # check if token id of token got from request exists
    check_token_id = (
        user_verify_token_ids_query.filter(
            auth_model.UserVerificationCodeToken.code_token_id == token_claims.token_id,
            auth_model.UserVerificationCodeToken.is_deleted == False,
        )
        .order_by(desc(auth_model.UserVerificationCodeToken.created_at))
        .first()
    )

    if not check_token_id:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User verification failed, Reset token not found",
        )

    try:
        # update is_deleted to True for all user verify tokens and blacklist all token ids
        user_verify_token_ids_query.update(
            {"is_deleted": True}, synchronize_session=False
        )
        user_verify_token_ids = [
            item.code_token_id for item in user_verify_token_ids_query.all()
        ]

        # update is_verified to True, status to ACT in user
        user_query.update(
            {"status": "ACT", "is_verified": True},
            synchronize_session=False,
        )

        # create an entry in guidelines_violation_score
        add_guideline_violation_score = admin_model.GuidelineViolationScore(
            user_id=user.id
        )
        db.add(add_guideline_violation_score)

        db.commit()
        db.refresh(user)

        for token_id in user_verify_token_ids:
            auth_utils.blacklist_token(token=token_id)

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing user verification request",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": "User verified successfully, User account created.",
        "data": user,
    }


# password change routes
# password reset when forgot password
@router.post("/password/reset")
def reset_password(
    background_tasks: BackgroundTasks,
    user_email: EmailStr = Form(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
):
    reset_user = user_schema.UserPasswordReset(email=user_email)

    # check if user is valid using email
    user = user_service.get_user_by_email(
        email=reset_user.email, status_not_in_list=["PDI", "PDB", "DEL"], db_session=db
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in ("TBN", "PBN"):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # generate a token
    claims = {"sub": user.email, "role": user.type}
    reset_token, reset_token_id = auth_utils.create_reset_token(claims=claims)

    # generate reset link
    reset_link = f"https://vpkonnect.in/accounts/password/change/?token={reset_token}"

    email_subject = "VPKonnect - Password Reset Request"

    # send mail with reset link if user is valid, we will using mailtrap dummy server for testing
    email_details = admin_schema.SendEmail(
        template="password_reset_email.html",
        email=[reset_user.email],
        body_info={
            "username": user.username,
            "link": reset_link,
            "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
        },
    )

    # add the token id to user verification code token table
    add_reset_token_id = auth_model.UserVerificationCodeToken(
        code_token_id=reset_token_id,
        type="PWR",
        user_id=user.id,
    )

    try:
        db.add(add_reset_token_id)
        db.commit()

        email_utils.send_email(email_subject, email_details, background_tasks)
    except SQLAlchemyError as exc:
        auth_utils.blacklist_token(reset_token)
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing reset password request",
        ) from exc
    except ConnectionErrors as exc:
        auth_utils.blacklist_token(reset_token)
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending mail",
        ) from exc
    except Exception as exc:
        auth_utils.blacklist_token(reset_token)
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"An email will be sent to {reset_user.email} if an account is registered under it."
    }


# password change using reset link
@router.post("/password/change")
def change_password_reset(
    background_tasks: BackgroundTasks,
    password: str = Form(),
    confirm_password: str = Form(),
    reset_token: str = Form(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
):
    reset = user_schema.UserPasswordChangeReset(
        password=password, confirm_password=confirm_password, reset_token=reset_token
    )

    # check both entered passwords
    if reset.password != reset.confirm_password:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    del confirm_password

    # get the token, decode it, verify it
    token_claims = auth_utils.verify_reset_token(token=reset.reset_token)

    # check token blacklist
    reset_token_blacklist_check = auth_utils.is_token_blacklisted(
        token=token_claims.token_id
    )
    if reset_token_blacklist_check:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Paswword reset failed, Token invalid/revoked",
        )

    # get the user
    user_query = user_service.get_user_by_email_query(
        email=token_claims.email,
        status_not_in_list=["PDB", "PDI", "DEL"],
        db_session=db,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in ("TBN", "PBN"):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # get query to fetch all reset token ids related to the user
    user_password_reset_tokens_query = (
        auth_service.get_user_verification_codes_tokens_query(
            user_id=str(user.id), _type="PWR", db_session=db
        )
    )

    # check if token id of token got in form request exists
    token_id_check = (
        user_password_reset_tokens_query.filter(
            auth_model.UserVerificationCodeToken.code_token_id == token_claims.token_id,
            auth_model.UserVerificationCodeToken.is_deleted == False,
        )
        .order_by(desc(auth_model.UserVerificationCodeToken.created_at))
        .first()
    )
    if not token_id_check:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Password reset failed, Reset token not found",
        )

    # send mail to inform password reset
    email_subject = "VPKonnect - Password Reset Notification"
    email_details = admin_schema.SendEmail(
        template="password_reset_change_notification.html",
        email=[EmailStr(user.email)],
        body_info={
            "username": user.username,
            "action": "reset",
            "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
        },
    )

    try:
        # update is_deleted to True for all reset tokens and blacklist all token ids
        user_password_reset_tokens_query.update(
            {"is_deleted": True}, synchronize_session=False
        )
        reset_token_ids = [
            item.code_token_id for item in user_password_reset_tokens_query.all()
        ]
        for token_id in reset_token_ids:
            auth_utils.blacklist_token(token=token_id)

        # hash the new password and update the password field in user table
        hashed_password = password_utils.get_hash(password=reset.password)
        user_query.update({"password": hashed_password}, synchronize_session=False)

        # add an entry to password change history table
        add_password_change_history_entry = user_model.PasswordChangeHistory(
            user_id=user.id
        )
        db.add(add_password_change_history_entry)
        db.commit()

        email_utils.send_email(email_subject, email_details, background_tasks)

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing change password request",
        ) from exc
    except ConnectionErrors as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending mail",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": "Password change successful"}


# update password
@router.post("/password/update")
@auth_utils.authorize(["user"])
def change_password_update(
    background_tasks: BackgroundTasks,
    old_password: str = Form(),
    new_password: str = Form(),
    confirm_new_password: str = Form(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    update = user_schema.UserPasswordChangeUpdate(
        old_password=old_password,
        new_password=new_password,
        confirm_new_password=confirm_new_password,
    )

    # get current user
    curr_auth_user_query = user_service.get_user_by_email_query(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    curr_auth_user = curr_auth_user_query.first()

    # check both old password and new password
    if update.old_password == update.new_password:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be same as Old Password",
        )

    # check old password
    old_password_check = password_utils.verify_password(
        entered_password=update.old_password, hashed_password=curr_auth_user.password
    )
    if not old_password_check:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Old password invalid"
        )

    # check both newly entered passwords
    if update.new_password != update.confirm_new_password:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    del confirm_new_password

    # send mail to inform password change
    email_subject = "VPKonnect - Password Change Notification"
    email_details = admin_schema.SendEmail(
        template="password_reset_change_notification.html",
        email=[EmailStr(curr_auth_user.email)],
        body_info={
            "username": curr_auth_user.username,
            "action": "updated",
            "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
        },
    )

    try:
        # hash the new password and update the password field in user table
        hashed_password = password_utils.get_hash(password=update.new_password)
        curr_auth_user_query.update(
            {"password": hashed_password}, synchronize_session=False
        )

        # add an entry to password change history table
        add_password_change_history_entry = user_model.PasswordChangeHistory(
            user_id=curr_auth_user.id
        )
        db.add(add_password_change_history_entry)
        db.commit()

        email_utils.send_email(email_subject, email_details, background_tasks)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing change password request",
        ) from exc
    except ConnectionErrors as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending mail",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"user": curr_auth_user.username, "message": "Password change successful"}


# follow/unfollow users
@router.post("/follow")
@auth_utils.authorize(["user"])
def follow_user(
    followed_user: user_schema.UserFollow,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get the user to be followed
    user_followed = user_service.get_user_by_username(
        username=followed_user.username,
        status_not_in_list=["PDI", "PDB", "DEL"],
        db_session=db,
    )
    if not user_followed:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User to be followed not found",
        )

    if user_followed.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User profile to be followed not found",
        )

    if user_followed.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User to be followed is banned, cannot access profile",
        )

    # get follower user
    follower_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # RSF cannot follow
    if follower_user.status == "RSF":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow/unfollow other user, user is under full restriction",
        )

    # user cannot follow/unfollow him/herself
    if followed_user.username == follower_user.username:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="User cannot follow/unfollow itself",
        )

    # get followed user's followers
    following_usernames = [
        follower_association.follower.username
        for follower_association in user_followed.followers
    ]

    message = None
    try:
        # follow a user
        if followed_user.action == "follow":
            # check if already follows the user
            if follower_user.username in following_usernames:
                raise HTTPException(
                    status_code=http_status.HTTP_409_CONFLICT,
                    detail=f"You already are following {user_followed.username}",
                )

            # if user is private then send request orelse follow directly
            if user_followed.account_visibility == "PRV":  # type: ignore
                # check if follow request already sent
                check_request_sent = (
                    user_service.get_user_follow_association_entry_query(
                        follower_id=str(follower_user.id),
                        followed_id=str(user_followed.id),
                        status="PND",
                        db_session=db,
                    )
                )
                if check_request_sent.first():
                    raise HTTPException(
                        status_code=http_status.HTTP_409_CONFLICT,
                        detail="Follow request is already sent",
                    )

                follow_request = user_model.UserFollowAssociation(
                    status="PND",
                    follower=follower_user,
                    followed=user_followed,
                )
                db.add(follow_request)

                message = f"Follow request sent to {followed_user.username}"
            else:
                follow = user_model.UserFollowAssociation(
                    status="ACP",
                    follower=follower_user,
                    followed=user_followed,
                )
                db.add(follow)

                message = f"Following {followed_user.username}"

        # unfollow a user
        elif followed_user.action == "unfollow":
            # check if follows the user
            if follower_user.username not in following_usernames:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"You are not following {user_followed.username}",
                )
            # get user follow entry query
            user_follow_query = user_service.get_user_follow_association_entry_query(
                follower_id=str(follower_user.id),
                followed_id=str(user_followed.id),
                status="ACP",
                db_session=db,
            )
            if not user_follow_query.first():
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="User follow entry not found",
                )

            # update the status to unfollowed
            user_follow_query.update(
                {"status": "UNF"},
                synchronize_session=False,
            )

            print(following_usernames)
            message = f"Unfollowed {followed_user.username}"

        db.commit()
    except HTTPException as exc:
        db.rollback()
        raise exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing follow/unfollow user request",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": message}


# accept/reject follow request
@router.put("/follow/requests/{username}")
@auth_utils.authorize(["user"])
def manage_follow_request(
    username: str,
    follow_request: user_schema.UserFollowRequest,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # check for user using username
    follower_user = user_service.get_user_by_username(
        username=username,
        status_not_in_list=["PDI", "PDB", "DEL"],
        db_session=db,
    )
    if not follower_user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Follower user not found"
        )
    if follower_user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Follower user profile not found",
        )
    if follower_user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Follower user is banned, cannot access profile",
        )

    # get current user object
    user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # check for user follow entry with status pending
    user_follow_query = user_service.get_user_follow_association_entry_query(
        follower_id=str(follower_user.id),
        followed_id=str(user.id),
        status="PND",
        db_session=db,
    )
    if not user_follow_query.first():
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User follow entry not found",
        )

    message = None
    try:
        # accept the follow request
        if follow_request.action == "accept":
            user_follow_query.update(
                {
                    "status": "ACP",
                    "follower_user_id": follower_user.id,
                    "followed_user_id": user.id,
                },
                synchronize_session=False,
            )

            message = f"Following {user.username}"

        # reject the follow request
        elif follow_request.action == "reject":
            user_follow_query.update(
                {
                    "status": "REJ",
                    "follower_user_id": follower_user.id,
                    "followed_user_id": user.id,
                },
                synchronize_session=False,
            )

            message = f"Rejected the request to follow {user.username}"

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing accept/reject follow requests",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": message}


# get all followers/following of a user
@router.get(
    "/{username}/follow",
    response_model=list[user_schema.UserFollowersFollowingResponse],
)
@auth_utils.authorize(["user"])
def get_user_followers_following(
    username: str,
    fetch: Literal["followers", "following"] = Query(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get user from username
    user = user_service.get_user_by_username(
        username=username,
        status_not_in_list=["PDI", "PDB", "DEL"],
        db_session=db,
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    if user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is banned, cannot access profile",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get details only if owner or public account or follower
    follower_check = user_service.check_user_follower_or_not(
        follower_id=str(curr_auth_user.id), followed_id=str(user.id), db_session=db
    )

    if (username != curr_auth_user.username) and (user.account_visibility == "PRV" and not follower_check):  # type: ignore
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # check the fetch
    followers_list = []
    following_list = []
    curr_auth_user_following_usernames = (
        following_association.followed.username
        for following_association in curr_auth_user.following
    )
    if fetch == "followers":
        user_followers = (
            follower_association.follower for follower_association in user.followers
        )
        for follower in user_followers:
            if follower.username in curr_auth_user_following_usernames:
                followers_list.append(
                    {
                        "profile_picture": follower.profile_picture,
                        "username": follower.username,
                        "follows_user": True,
                    }
                )
            else:
                if follower.username == curr_auth_user.username:
                    followers_list.append(
                        {
                            "profile_picture": follower.profile_picture,
                            "username": follower.username,
                            "follows_user": None,
                        }
                    )
                else:
                    followers_list.append(
                        {
                            "profile_picture": follower.profile_picture,
                            "username": follower.username,
                            "follows_user": False,
                        }
                    )

        return followers_list

    elif fetch == "following":
        user_following = (
            following_association.followed for following_association in user.following
        )
        for following in user_following:
            if following.username in curr_auth_user_following_usernames:
                following_list.append(
                    {
                        "profile_picture": following.profile_picture,
                        "username": following.username,
                        "follows_user": True,
                    }
                )
            else:
                if following.username == curr_auth_user.username:
                    following_list.append(
                        {
                            "profile_picture": following.profile_picture,
                            "username": following.username,
                            "follows_user": None,
                        }
                    )
                else:
                    following_list.append(
                        {
                            "profile_picture": following.profile_picture,
                            "username": following.username,
                            "follows_user": False,
                        }
                    )

        return following_list

    else:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Error processing request. Invalid fetch",
        )


# get all follow requests of user
@router.get(
    "/follow/requests",
    response_model=list[user_schema.UserGetFollowRequestsResponse],
)
@auth_utils.authorize(["user"])
def get_follow_requests(
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get all follow requests
    user_follow_requests_entries = user_service.get_user_follow_requests(
        followed_id=str(curr_auth_user.id), status="PND", db_session=db
    )

    requests_user_ids = [
        entry.follower_user_id for entry in user_follow_requests_entries
    ]
    requests_users = (
        db.query(user_model.User.profile_picture, user_model.User.username)
        .filter(
            user_model.User.id.in_(requests_user_ids),
            user_model.User.status.in_(
                [
                    "ACT",
                    "INA",
                    "RSF",
                    "RSP",
                    "TBN",
                ]
            ),
            user_model.User.is_verified == True,
            user_model.User.is_deleted == False,
        )
        .all()
    )

    return requests_users


# remove a follower
@router.put("/follow/remove/{username}")
@auth_utils.authorize(["user"])
def remove_follower(
    username: str,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get user from username
    follower_user = user_service.get_user_by_username(
        username=username, status_not_in_list=["PDI", "PDB", "DEL"], db_session=db
    )
    if not follower_user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Follower user not found"
        )

    if follower_user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Follower user profile not found",
        )

    if follower_user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Follower user is banned, cannot access profile",
        )

    # get curr user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the user follow association entry
    user_follow_entry_query = user_service.get_user_follow_association_entry_query(
        follower_id=follower_user.id,
        followed_id=curr_auth_user.id,
        status="ACP",
        db_session=db,
    )
    user_follow_entry = user_follow_entry_query.first()
    if not user_follow_entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User follow entry not found",
        )

    try:
        # update the follow entry status from ACP to RMV
        user_follow_entry_query.update(
            {
                "status": "RMV",
                "follower_user_id": user_follow_entry.follower_user_id,
                "followed_user_id": user_follow_entry.followed_user_id,
            },
            synchronize_session=False,
        )

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing remove follower request",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"{follower_user.username} has been removed from your followers successfully"
    }


# update username
@router.post("/username/change")
@auth_utils.authorize(["user"])
def username_change(
    new_username: str = Form(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    update = user_schema.UserUsernameChange(new_username=new_username)

    # get current user
    curr_auth_user_query = user_service.get_user_by_email_query(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )
    curr_auth_user = curr_auth_user_query.first()

    # check if new username matches old username
    if update.new_username == curr_auth_user.username:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="New username cannot be same as old username",
        )

    # check if new username already taken
    username_exists = user_service.check_username_exists(
        username=update.new_username, db_session=db
    )
    if username_exists:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=f"Username {update.new_username} is already taken",
        )

    try:
        # update username
        curr_auth_user_query.update(
            {"username": update.new_username}, synchronize_session=False
        )

        # add entry to username change history table
        add_username_change_history_entry = user_model.UsernameChangeHistory(
            previous_username=curr_auth_user.username, user_id=curr_auth_user.id
        )

        db.add(add_username_change_history_entry)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing username change request",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": "Username change successful"}


# get user profile
@router.get("/{username}/profile")
@auth_utils.authorize(["user"])
def user_profile(
    username: str,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get the user from username
    user = user_service.get_user_by_username(
        username=username,
        status_not_in_list=["DEL", "PDB", "PDI"],
        db_session=db,
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    elif user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )
    elif user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is banned, cannot access profile",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # check whether current user follows user or not
    follower_check = user_service.check_user_follower_or_not(
        follower_id=str(curr_auth_user.id), followed_id=str(user.id), db_session=db
    )

    # show dp, username, no of posts, no of followers and following, followed_by, follows_user, message
    # posts will be fetched by all posts api endpoint
    # get no. of posts
    no_of_posts = post_service.count_posts(user_id=user.id, status="PUB", db_session=db)

    # get no of followers and following
    no_of_followers = user_service.count_followers(
        user_id=user.id, status="ACP", db_session=db
    )
    no_of_following = user_service.count_following(
        user_id=user.id, status="ACP", db_session=db
    )

    # U1, U2, U3, U4, U5 are users
    # get those users who are followed by U1 and follow U4
    # U1 is following U2, U3, U5
    # U2 and U3 are following U4
    # output: U2 and U3
    followed_by_objs = user_service.user_followed_by(
        current_user_id=curr_auth_user.id, profile_user_id=user.id, db_session=db
    )
    followed_by = (
        [followed_user.followed.username for followed_user in followed_by_objs]
        if username != curr_auth_user.username
        else None
    )

    follows_user = True if follower_check else False

    user_profile_details = user_schema.UserProfileResponse(
        username=user.username,
        profile_picture=user.profile_picture,
        num_of_posts=no_of_posts,
        num_of_followers=no_of_followers,
        num_of_following=no_of_following,
        bio=user.bio,
        followed_by=followed_by,
        follows_user=follows_user if username != curr_auth_user.username else None,
    )

    return user_profile_details


# get all user posts
@router.get(
    "/{username}/posts",
)
@auth_utils.authorize(["user"])
def get_all_user_posts(
    username: str,
    status: Literal["published", "draft", "banned", "flagged_banned"] = Query(),
    limit: int = Query(3, le=12),
    last_post_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # transform status
    try:
        post_status = map_utils.transform_status(value=status)
    except HTTPException as exc:
        raise exc

    # get the user from username
    user = user_service.get_user_by_username(
        username=username,
        status_not_in_list=["DEL", "PDB", "PDI"],
        db_session=db,
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    elif user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )
    elif user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is banned, cannot access profile",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # check whether current user follows user or not
    follower_check = user_service.check_user_follower_or_not(
        follower_id=str(curr_auth_user.id), followed_id=str(user.id), db_session=db
    )

    if username != curr_auth_user.username:
        if user.account_visibility == "PRV" and not follower_check:
            return {"message": "This profile is private. Follow to see their posts."}

        elif post_status in ("DRF", "FLB", "BAN"):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access requested resource",
            )

    # get the posts
    all_posts = post_service.get_all_posts_profile(
        profile_user_id=user.id,
        status=post_status,
        limit=limit,
        last_post_id=last_post_id,
        db_session=db,
    )

    if not all_posts:
        if last_post_id:
            return {"message": "No more posts available", "info": "Done"}

        return {"message": "No posts yet"}

    all_posts_response = [
        post_schema.PostProfileResponse(
            id=post.id,
            image=post.image,
            num_of_likes=(
                post_service.count_post_likes(
                    post_id=post.id, status="ACT", db_session=db
                )
                if post.status != "DRF"
                else None
            ),
            num_of_comments=(
                comment_service.count_comments(
                    post_id=post.id, status_in_list=["PUB", "FLB"], db_session=db
                )
                if post.status != "DRF"
                else None
            ),
        )
        for post in all_posts
    ]

    return all_posts_response


# user feed
@router.get("/feed")
@auth_utils.authorize(["user"])
def user_feed(
    db: Session = Depends(get_db),
    last_seen_post_id: UUID = Query(None),
    limit: int = Query(3, le=10),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the user following ids
    user_following_ids = user_service.get_user_following_ids(
        user_id=curr_auth_user.id, db_session=db
    )

    if not user_following_ids:
        return {"message": "Follow people to get their updates"}

    # get all posts upto 3 days ago
    user_feed_posts, next_cursor = post_service.get_all_posts_user_feed(
        followed_user_id_list=user_following_ids,
        last_seen_post_id=last_seen_post_id,
        limit=limit,
        db_session=db,
    )

    if not user_feed_posts:
        return {"message": "You have completely caught up from the past 3 days"}

    user_feed_posts_response = [
        post_schema.PostUserFeedResponse(
            id=post.id,
            image=post.image,
            num_of_likes=post_service.count_post_likes(
                post_id=post.id, status="ACT", db_session=db
            ),
            num_of_comments=comment_service.count_comments(
                post_id=post.id, status_in_list=["PUB", "FLB"], db_session=db
            ),
            post_user=post.post_user,
            caption=post.caption,
            posted_time_ago=basic_utils.time_ago(post_datetime=post.created_at),
            curr_user_like=post_service.user_like_exists(
                user_id=curr_auth_user.id, post_id=post.id, db_session=db
            )
            is not None,  # OR any(like.post_like_user.username for like in post.likes)
        )
        for post in user_feed_posts
    ]

    user_feed_response = user_schema.UserFeedResponse(
        posts=user_feed_posts_response, next_cursor=next_cursor
    )

    return user_feed_response


# deactivate/soft-delete the user account
@router.patch("/deactivate")
@auth_utils.authorize(["user"])
def deactivate_or_soft_delete_user(
    background_tasks: BackgroundTasks,
    password: str = Form(None),
    action: Literal["deactivate", "delete"] = Query(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user_query = user_service.get_user_by_email_query(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )
    curr_auth_user = curr_auth_user_query.first()

    # check for password in the request
    if not password:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="Password required"
        )

    # create object
    deactivate_delete_request = user_schema.UserDeactivationDeletion(password=password)

    # check if password is right
    password_check = password_utils.verify_password(
        entered_password=deactivate_delete_request.password,
        hashed_password=curr_auth_user.password,
    )
    if not password_check:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    message = None
    try:
        # check action
        if action == "deactivate":
            # update status of the user
            curr_auth_user.status = "DAH"

            message = f"Your @{curr_auth_user.username} account has been deactivated successfully"

        elif action == "delete":
            # send mail informing user about the account deletion, we will using mailtrap dummy server for testing
            email_subject = "Your VPKonnect account is scheduled for deletion"
            email_details = admin_schema.SendEmail(
                template="account_deletion_email.html",
                email=[curr_auth_user.email],
                body_info={
                    "username": curr_auth_user.username,
                    "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
                },
            )

            # update status to pending_deletion_(hide/keep)
            curr_auth_user.status = "PDH"

            message = f"Your account deletion request is accepted. @{curr_auth_user.username} account will be deleted after a deactivation period of 30 days. An email for the same has been sent to {user.email}"
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Error processing request",
            )

        db.commit()

        if action == "delete":
            email_utils.send_email(email_subject, email_details, background_tasks)

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing deactivate/delete user request",
        ) from exc
    except ConnectionErrors as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending mail",
        ) from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": message}


# report an item
@router.post("/report")
@auth_utils.authorize(["user"])
def report_item(
    reported_item: user_schema.UserContentReport,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # check if item is there or not
    if reported_item.item_type == "post":
        post = post_service.get_a_post(
            str(reported_item.item_id), ["DRF", "HID", "RMV", "FLD"], db
        )
        if not post:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Post not found"
            )
        if post.status == "BAN":
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Post already banned",
            )
        if post.status == "FLB":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported post already flagged to be banned",
            )

    elif reported_item.item_type == "comment":
        comment = comment_service.get_a_comment(
            str(reported_item.item_id), ["HID", "RMV", "FLD"], db
        )
        if not comment:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if comment.status == "BAN":
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comment already banned",
            )
        if comment.status == "FLB":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported comment already flagged to be banned",
            )

    # get the reporter and reported user
    reporter_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )
    reported_user = user_service.get_user_by_username(
        username=reported_item.username,
        status_not_in_list=["DEL", "PDI", "PDB"],
        db_session=db,
    )
    if not reported_user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Reported user not found"
        )
    if reported_user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Reported user profile not found",
        )
    if reported_user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Reported user is already permanently banned",
        )

    report_reason_user = None
    if reported_item.item_type == "account":
        reported_item.item_id = reported_user.id

        # if impersonation report where username is specified
        if reported_item.reason_username:
            report_reason_user = user_service.get_user_by_username(
                username=reported_item.reason_username,
                status_not_in_list=["DEL", "PDI", "PDB"],
                db_session=db,
            )
            if not report_reason_user:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Original user of impersonating user not found",
                )
            if report_reason_user.status in ("DAH", "PDH"):
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Original user profile of impersonating user not found",
                )
            if reported_user.status == "PBN":
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Original user of impersonating user is already permanently banned",
                )

    # user cannot report his/her own item
    if reporter_user.username == reported_user.username:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User cannot report own content",
        )

    # check table if report exists of same user for same item and same reason
    same_user_report = user_service.check_if_same_report_exists(
        user_id=reporter_user.id,
        content_id=str(reported_item.item_id),
        report_reason=reported_item.reason,
        db_session=db,
    )
    if same_user_report:
        return {
            "message": f"This {reported_item.item_type} has already been reported by you with {reported_item.reason}."
        }

    # add the report to table
    user_report = admin_model.UserContentReportDetail(
        reporter_user_id=reporter_user.id,
        reported_item_id=reported_item.item_id,
        reported_item_type=reported_item.item_type,
        reported_user_id=reported_user.id,
        report_reason=reported_item.reason,
        report_reason_user_id=report_reason_user.id if report_reason_user else None,
    )

    try:
        db.add(user_report)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error proccesing report item request",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"This {reported_item.item_type} has been reported anonymously and will be handled by content moderator."
    }


# appeal for a content
@router.post("/appeal")
def appeal_content(
    appeal_user_request: user_schema.UserContentAppeal = FormDepends(
        user_schema.UserContentAppeal
    ),  # type: ignore
    attachment: UploadFile | None = None,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
):
    restrict_ban_entry = None
    report_entry = None

    if appeal_user_request.content_type == "account":
        # get the user using username and email
        appeal_user = user_service.get_user_by_username_email(
            username=appeal_user_request.username,
            email=appeal_user_request.email,
            status_in_list=["TBN", "PBN", "RSP", "RSF", "PDB", "DAH", "PDH", "INA"],
            db_session=db,
        )
        if not appeal_user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Appeal user not restricted/banned or maybe deleted",
            )

        appeal_user_request.content_id = appeal_user.id

        # check if 21 days appeal limit is crossed, status for this is PDB
        if appeal_user.status == "PDB":
            raise HTTPException(
                status_code=http_status.HTTP_410_GONE,
                detail="Your account has been permanently deleted because it did not follow our community guidelines. This decision cannot be reversed either because we have already reviewed it, or because 30 days have passed since your account was permanently banned.",
            )

        # get the active ban entry
        restrict_ban_entry = admin_service.get_user_active_restrict_ban_entry(
            user_id=appeal_user.id,
            db_session=db,
        )
        if not restrict_ban_entry:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Appeal user active restrict/ban entry not found",
            )

        # update user status if status is DAH/PDH/INA and active ban status is TBN/PBN
        if appeal_user.status in (
            "DAH",
            "PDH",
            "INA",
        ) and restrict_ban_entry.status in ("TBN", "PBN"):
            appeal_user.status = restrict_ban_entry.status

        # check if any previous rejected appeal for account appealed here associated with same report
        previous_rejected_appeal = admin_service.get_a_appeal_report_id_content_id(
            report_id=restrict_ban_entry.report_id,
            content_id=appeal_user_request.content_id,
            content_type=[appeal_user_request.content_type],
            status="REJ",
            db_session=db,
        )
        if previous_rejected_appeal:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Request to appeal this account has been denied. Further appeals are not permitted after a previous rejection",
            )

    # if post/comment
    elif appeal_user_request.content_type in ("post", "comment"):
        appeal_user = user_service.get_user_by_username_email(
            username=appeal_user_request.username,
            email=appeal_user_request.email,
            status_in_list=["ACT", "RSP", "RSF"],
            db_session=db,
        )
        if not appeal_user:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Appeal user not found",
            )

        # check if 28 days appeal limit is crossed or not
        if appeal_user_request.content_type == "post":
            post_appeal_submit_limit_expiry = (
                db.query(post_model.Post)
                .filter(
                    post_model.Post.id == appeal_user_request.content_id,
                    func.now()
                    >= (
                        post_model.Post.updated_at
                        + timedelta(days=settings.content_appeal_submit_limit_days)
                    ),
                    post_model.Post.is_deleted == False,
                )
                .first()
            )
            if post_appeal_submit_limit_expiry:
                raise HTTPException(
                    status_code=http_status.HTTP_410_GONE,
                    detail="This post is permanently banned and cannot be appealed for review. This decision cannot be reversed because 28 days have passed since your post was banned.",
                )

        elif appeal_user_request.content_type == "comment":
            comment_appeal_submit_limit_expiry = (
                db.query(comment_model.Comment)
                .filter(
                    comment_model.Comment.id == appeal_user_request.content_id,
                    func.now()
                    >= (
                        comment_model.Comment.updated_at
                        + timedelta(days=settings.content_appeal_submit_limit_days)
                    ),
                    comment_model.Comment.is_deleted == False,
                )
                .first()
            )
            if comment_appeal_submit_limit_expiry:
                raise HTTPException(
                    status_code=http_status.HTTP_410_GONE,
                    detail="This comment is permanently banned and cannot be appealed for review. This decision cannot be reversed because 28 days have passed since your comment was banned.",
                )

        # check if the post/comment is really banned/deleted or not
        if appeal_user_request.content_type == "post":
            banned_post = post_service.get_a_post(
                post_id=str(appeal_user_request.content_id),
                status_not_in_list=["PUB", "DRF", "HID", "FLB", "RMV", "FLD"],
                db_session=db,
            )
            if not banned_post:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Appealed post not banned",
                )

        elif appeal_user_request.content_type == "comment":
            banned_comment = comment_service.get_a_comment(
                comment_id=str(appeal_user_request.content_id),
                status_not_in_list=["PUB", "HID", "FLB", "FLD", "RMV"],
                db_session=db,
            )
            if not banned_comment:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Appealed comment not banned",
                )
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Invalid content type",
            )

        # check if any previous rejected appeal for post/comment appealed here associated with same report
        previous_rejected_appeal = admin_service.get_a_appeal_report_id_content_id(
            report_id=None,
            content_id=appeal_user_request.content_id,  # type: ignore
            content_type=[appeal_user_request.content_type],
            status="REJ",
            db_session=db,
        )
        if previous_rejected_appeal:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=f"Request to appeal this {appeal_user_request.content_type} has been denied. Further appeals are not permitted after a previous rejection",
            )

        # get the report entry
        report_entry = admin_service.get_a_latest_report_by_content_id_user_id(
            user_id=appeal_user.id,
            content_id=appeal_user_request.content_id,  # type: ignore
            content_type=appeal_user_request.content_type,
            status="RSD",
            db_session=db,
        )

        if not report_entry:
            # check the content in account_report_flagged_content table and get the entry
            flagged_content_entry = admin_service.get_account_report_flagged_content_entry_valid_flagged_content_id(
                content_id=appeal_user_request.content_id, db_session=db  # type: ignore
            )
            if not flagged_content_entry:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Report associated with appeal content not found",
                )

            # check if the report associated with the flagged content is RSD or not
            resolved_flagged_content_entry = (
                admin_service.get_a_report_by_report_id_query(
                    report_id=flagged_content_entry.report_id,
                    status="RSD",
                    db_session=db,
                ).first()
            )
            if not resolved_flagged_content_entry:
                raise HTTPException(
                    status_code=http_status.HTTP_404_NOT_FOUND,
                    detail="Report associated with appeal content not found",
                )

            report_entry = resolved_flagged_content_entry
    else:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="Invalid content type"
        )

    ban_report_id = uuid4()
    if restrict_ban_entry:
        ban_report_id = restrict_ban_entry.report_id
    elif report_entry:
        ban_report_id = report_entry.id

    # add the appeal
    new_appeal = admin_model.UserContentRestrictBanAppealDetail(
        user_id=appeal_user.id,
        report_id=ban_report_id,
        content_type=appeal_user_request.content_type,
        content_id=appeal_user_request.content_id,
        appeal_detail=appeal_user_request.detail,
    )

    image_path = None
    try:
        if attachment:
            # image validation and handling
            image_name = image_utils.validate_image_generate_name(
                username=appeal_user.username,
                image=attachment,
                logger=logger,
            )

            new_appeal.attachment = image_name

            # get appeals subfolder
            appeals_subfolder = (
                image_folder / "user" / str(appeal_user.repr_id) / "appeals"
            )

            image_path = appeals_subfolder / image_name

            # write image to target
            image_utils.write_image(
                image=attachment,
                image_path=image_path,
                logger=logger,
            )

        db.add(new_appeal)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if attachment and image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting appeal",
        ) from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if attachment and image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"Your appeal for {appeal_user_request.content_type} {'@'+ appeal_user.username if appeal_user_request.content_type == 'account' else appeal_user_request.content_id} has been submitted successfully and will be handled by content moderator."
    }


# for internal jobs involving bans only, send ban email
@router.post("/send-ban-mail")
def send_ban_mail(
    email_parameters: admin_schema.UserSendBanEmail,
    background_tasks: BackgroundTasks,
):
    # generate appeal link
    appeal_link = "https://vpkonnect.in/accounts/appeals/form_ban"

    email_subject = "VPKonnect - Account Ban"
    email_details = admin_schema.SendEmail(
        template=(
            "permanent_ban_email.html"
            if email_parameters.status == "PBN"
            else "temporary_ban_email.html"
        ),
        email=[EmailStr(email_parameters.email)],
        body_info={
            "username": email_parameters.username,
            "link": appeal_link,
            "days": email_parameters.duration // 24,
            "ban_enforced_datetime": email_parameters.enforced_action_at.strftime(
                "%b %d, %Y %H:%M %Z"
            ),
            "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
        },
    )

    try:
        email_utils.send_email(
            email_subject=email_subject,
            email_details=email_details,
            bg_tasks=background_tasks,
        )
    except ConnectionErrors as exc:
        raise exc
    except Exception as exc:
        raise exc


# for internal jobs involving delete only, send delete email
@router.post("/send-delete-mail")
def send_delete_mail(
    email_request: admin_schema.UserSendDeleteEmail,
    background_tasks: BackgroundTasks,
):
    # generate data link
    data_link = "https://vpkonnect.in/accounts/data_request_form"

    email_subject = email_request.subject
    email_details = admin_schema.SendEmail(
        template=email_request.template,
        email=email_request.email,
        body_info={
            "link": data_link,
            "logo": basic_utils.image_to_base64(Path("vpkonnect.png")),
        },
    )

    try:
        email_utils.send_email(
            email_subject=email_subject,
            email_details=email_details,
            bg_tasks=background_tasks,
        )
    except ConnectionErrors as exc:
        raise exc
    except Exception as exc:
        raise exc


# user violation status
@router.get("/violation")
@auth_utils.authorize(["user"])
def get_user_violation_status_details(
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get violation details
    violation_details = admin_service.get_user_violation_details(
        user_id=curr_auth_user.id, db_session=db
    )

    # get active restrict/ban if any
    active_restrict_ban = admin_service.get_user_active_restrict_ban_entry(
        user_id=curr_auth_user.id, db_session=db
    )

    # get guideline violation score
    guideline_violation_score = admin_service.get_user_guideline_violation_score_query(
        user_id=curr_auth_user.id, db_session=db
    ).one()

    # violation details response
    violation_details_response = user_schema.UserViolationDetailResponse(
        num_of_post_violations_no_restrict_ban=violation_details.num_of_post_violations_no_restrict_ban,
        num_of_comment_violations_no_restrict_ban=violation_details.num_of_comment_violations_no_restrict_ban,
        num_of_account_violations_no_restrict_ban=violation_details.num_of_account_violations_no_restrict_ban,
        total_num_of_violations_no_restrict_ban=violation_details.total_num_of_violations_no_restrict_ban,
        num_of_partial_account_restrictions=violation_details.num_of_partial_account_restrictions,
        num_of_full_account_restrictions=violation_details.num_of_full_account_restrictions,
        num_of_account_temporary_bans=violation_details.num_of_account_temporary_bans,
        num_of_account_permanent_bans=violation_details.num_of_account_permanent_bans,
        total_num_of_account_restrict_bans=violation_details.total_num_of_account_restrict_bans,
        active_restrict_ban=active_restrict_ban,
        violation_score=guideline_violation_score.final_violation_score,
    )

    return {f"{curr_auth_user.username} violation details": violation_details_response}


# about user
@router.get("/{username}/about")
@auth_utils.authorize(["user"])
def about_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the user from username
    user = user_service.get_user_by_username(
        username=username,
        status_not_in_list=["DEL", "PDB", "PDI"],
        db_session=db,
    )
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    elif user.status in ("DAH", "PDH"):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )
    elif user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is banned, cannot access profile",
        )

    if curr_auth_user.username == username:
        user_response = user_schema.UserAboutResponse(
            profile_picture=user.profile_picture,
            username=user.username,
            account_created_on=user.created_at,
            account_based_in=user.country,
            former_usernames=[item.previous_username for item in user.usernames],
            num_of_former_usernames=len(user.usernames),
        )
    else:
        user_response = user_schema.UserAboutResponse(
            profile_picture=user.profile_picture,
            username=user.username,
            account_created_on=user.created_at,
            account_based_in=user.country,
        )

    return user_response
