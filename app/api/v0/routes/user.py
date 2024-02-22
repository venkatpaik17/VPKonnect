import shutil
from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from PIL import Image, UnidentifiedImageError
from pydantic import EmailStr
from pyfa_converter import FormDepends
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import admin as admin_model
from app.models import auth as auth_model
from app.models import user as user_model
from app.schemas import admin as admin_schema
from app.schemas import auth as auth_schema
from app.schemas import user as user_schema
from app.services import auth as auth_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import email as email_utils
from app.utils import image as image_utils
from app.utils import password as password_utils

router = APIRouter(prefix=settings.api_prefix + "/users", tags=["Users"])

MAX_SIZE = 5 * 1024 * 1024


@router.post("/register", status_code=status.HTTP_201_CREATED)
def create_user(
    background_tasks: BackgroundTasks,
    request: user_schema.UserRegister = FormDepends(user_schema.UserRegister),  # type: ignore
    db: Session = Depends(get_db),
    image: UploadFile | None = None,
):
    # check if user registered but unverified
    unverified_user_query = user_service.get_user_by_email_query(
        request.email,
        [
            "ACT",
            "DAH",
            "DAK",
            "RSF",
            "RSP",
            "TBN",
            "PDH",
            "PDK",
            "PBN",
            "DEL",
        ],
        db,
    )
    unverified_user = unverified_user_query.filter(
        user_model.User.is_verified == False
    ).first()
    if unverified_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with {unverified_user.email} already registered. Verification Pending.",
        )

    # check both entered passwords are same
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del request.confirm_password

    username_check = user_service.check_username_exists(request.username, db)
    if username_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username {request.username} is already taken",
        )
    user_check = user_service.check_user_exists(request.email, db)
    if user_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{request.email} already exists in the system",
        )

    hashed_password = password_utils.get_hash(request.password)
    request.password = hashed_password

    # image related code
    # if there is image uploaded, create a subfolder for profile pics, if folder exists get it. Upload the image in this folder.
    if image:
        # handling image validatity and unsupported types
        try:
            # we try to open the image, raises UnidentifiedImageError when image doesn't open
            with Image.open(image.file) as img:
                # verifies the image for any tampering/corruption, raises exception if verification fails
                img.verify()

            # move file pointer to the beginning of the file
            image.file.seek(0)

            # read the image file and check file size
            # img_read = image.file.read()
            # print(len(img_read))

            # Move to the end of the file, get image size, no need to read the file
            image.file.seek(0, 2)
            image_size = image.file.tell()

            # move file pointer to the beginning of the file
            image.file.seek(0)
            print(image_size)

            # if len(img_read) > MAX_SIZE: if image is read, we need to get the size using len()
            if image_size > MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too large, you can upload upto 5 MiB",
                )
        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format"
            ) from exc
        except HTTPException as exc:
            raise exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing image"
            ) from exc

        # db transaction, we flush the user with customized image filename and use user id as name for user subfolder
        # If everything goes right then only we commit. Any exceptions, rollback.
        try:
            upload_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
            image_name = f"{request.username}_{upload_datetime}_{image.filename}"

            add_user = user_model.User(**request.dict(), profile_picture=image_name)  # type: ignore
            db.add(add_user)
            db.flush()

            # create a subfolder for user specific uploads, if folder exists get it.
            user_subfolder = image_utils.get_or_create_entity_image_subfolder(
                "user", str(add_user.repr_id)
            )

            # create a subfolder for profile images, if folder exists get it.
            profile_subfolder = (
                image_utils.get_or_create_entity_profile_image_subfolder(user_subfolder)
            )

            image_path = profile_subfolder / image_name

            with open(image_path, "wb+") as f:
                shutil.copyfileobj(image.file, f)

            db.commit()
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registering user",
            ) from exc

    else:
        add_user = user_model.User(**request.dict())
        db.add(add_user)
        db.commit()

        # store image directly in the DB
        # add_user = user_model.User(**request.dict(), profile_picture=image.file.read())

        db.refresh(add_user)

    # generate a token
    claims = {"sub": add_user.email, "role": add_user.type}
    user_verify_token, user_verify_token_id = auth_utils.create_user_verify_token(
        claims
    )

    # generate verification link
    verify_link = (
        f"https://vpkonnect.in/accounts/signup/verify/?token={user_verify_token}"
    )

    try:
        email_subject = "VPKonnect - User Verification - Account Signup"
        email_details = admin_schema.SendEmail(
            template="user_account_signup_verification.html",
            email=[EmailStr(add_user.email)],
            body_info={"first_name": add_user.first_name, "link": verify_link},
        )
        # send email
        email_utils.send_email(email_subject, email_details, background_tasks)

        # add the token to userverificationcodetoken table
        add_user_verify_token = auth_model.UserVerificationCodeToken(
            code_token_id=user_verify_token_id,
            type="USV",
            user_id=add_user.id,
        )
        db.add(add_user_verify_token)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing verification email request",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending verification email.",
        ) from exc

    return {
        "message": f"User registration verification process - An email has been sent to {add_user.email} for verification."
    }


@router.post("/send-verify-email")
def send_verification_email_user(
    email_user_request: user_schema.UserSendEmail,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # get the user
    user = user_service.get_user_by_email(email_user_request.email, ["DEL"], db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # check the type and accordingly set parameters
    if email_user_request.type == "USV":
        if user.status in [
            "ACT",
            "DAH",
            "DAK",
            "RSF",
            "RSP",
            "TBN",
            "PDH",
            "PDK",
            "PBN",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to process your request at this time.",
            )

        # generate a token
        claims = {"sub": user.email, "role": user.type}
        user_token, token_id = auth_utils.create_user_verify_token(claims)

        # generate verification link
        verify_link = f"https://vpkonnect.in/accounts/signup/verify/?token={user_token}"
        email_subject = "VPKonnect - User Verification - Account Signup"
        email_details = admin_schema.SendEmail(
            template="user_account_signup_verification.html",
            email=[EmailStr(email_user_request.email)],
            body_info={
                "first_name": user.first_name,
                "link": verify_link,
            },
        )
        return_message = f"User registration verification process - An email has been sent to {user.email} for verification."

    elif email_user_request.type == "PWR":
        if user.status in [
            "TBN",
            "PBN",
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to process your request at this time. Please contact support for assistance.",
            )

        # generate token
        claims = {"sub": user.email, "role": user.type}
        user_token, token_id = auth_utils.create_reset_token(claims)

        # generate reset link
        reset_link = (
            f"https://vpkonnect.in/accounts/password/change/?token={user_token}"
        )

        email_subject = "VPKonnect - Password Reset Request"
        email_details = admin_schema.SendEmail(
            template="password_reset_email.html",
            email=[EmailStr(user.email)],
            body_info={"username": user.username, "link": reset_link},
        )
        return_message = f"An email will be sent to {user.email} if an account is registered under it."

    try:
        email_utils.send_email(email_subject, email_details, background_tasks)
        # add the token to userverificationcodetoken table
        add_user_token = auth_model.UserVerificationCodeToken(
            code_token_id=token_id,
            type="USV",
            user_id=user.id,
        )
        db.add(add_user_token)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing email request",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error sending email.",
        ) from exc

    return {"message": return_message}


@router.post("/register/verify", response_model=user_schema.UserVerifyResponse)
def verify_user_(user_verify_token: str = Form(), db: Session = Depends(get_db)):
    # decode token
    token_claims = auth_utils.verify_user_verify_token(user_verify_token)
    user_verify_token_blacklist_check = auth_utils.is_token_blacklisted(
        token_claims.token_id
    )
    if user_verify_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User verification failed, Token invalid/revoked",
        )

    # get the user
    user_query = user_service.get_user_by_email_query(
        token_claims.email,
        [
            "ACT",
            "DAH",
            "DAK",
            "RSF",
            "RSP",
            "TBN",
            "PDH",
            "PDK",
            "PBN",
            "DEL",
        ],
        db,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New user to be registered not found",
        )

    # get the query to fetch all user verify token ids related to the user
    user_verify_token_ids_query = auth_service.get_user_verification_codes_tokens_query(
        str(user.id), "USV", db
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
            status_code=status.HTTP_404_NOT_FOUND,
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

        for token_id in user_verify_token_ids:
            auth_utils.blacklist_token(token_id)

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

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing user verification request",
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
    user_email: str = Form(),
    db: Session = Depends(get_db),
):
    reset_user = user_schema.UserPasswordReset(email=user_email)
    # check if user is valid using email
    user = user_service.get_user_by_email(reset_user.email, ["DEL"], db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        "TBN",
        "PBN",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # generate a token
    claims = {"sub": user.email, "role": user.type}
    reset_token, reset_token_id = auth_utils.create_reset_token(claims)

    # generate reset link
    reset_link = f"https://vpkonnect.in/accounts/password/change/?token={reset_token}"

    email_subject = "VPKonnect - Password Reset Request"

    # send mail with reset link if user is valid, we will using mailtrap dummy server for testing
    try:
        email_details = admin_schema.SendEmail(
            template="password_reset_email.html",
            email=[reset_user.email],
            body_info={"username": user.username, "link": reset_link},
        )
        email_utils.send_email(email_subject, email_details, background_tasks)
    except Exception as exc:
        auth_utils.blacklist_token(reset_token)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error in sending email",
        ) from exc

    # add the token id to user password reset token table
    add_reset_token_id = auth_model.UserVerificationCodeToken(
        code_token_id=reset_token_id,
        type="PWR",
        user_id=user.id,
    )
    db.add(add_reset_token_id)
    db.commit()

    return {
        "message": f"An email will be sent to {reset_user.email} if an account is registered under it."
    }


# password change using reset link
@router.post("/password/change")
def change_password_reset(
    password: str = Form(),
    confirm_password: str = Form(),
    reset_token: str = Form(),
    db: Session = Depends(get_db),
):
    reset = user_schema.UserPasswordChangeReset(
        password=password, confirm_password=confirm_password, reset_token=reset_token
    )

    # check both entered passwords
    if reset.password != reset.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del confirm_password

    # get the token, decode it, verify it
    token_claims = auth_utils.verify_reset_token(reset.reset_token)

    # check token blacklist
    reset_token_blacklist_check = auth_utils.is_token_blacklisted(token_claims.token_id)
    if reset_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Paswword reset failed, Token invalid/revoked",
        )

    # get the user
    user_query = user_service.get_user_by_email_query(token_claims.email, ["DEL"], db)
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        "TBN",
        "PBN",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # get query to fetch all reset token ids related to the user
    user_password_reset_tokens_query = (
        auth_service.get_user_verification_codes_tokens_query(
            str(user.id),
            "PWR",
            db,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Password reset failed, Reset token not found",
        )
    try:
        # update is_deleted to True for all reset tokens and blacklist all token ids
        user_password_reset_tokens_query.update(
            {"is_deleted": True}, synchronize_session=False
        )
        reset_token_ids = [
            item.reset_token_id for item in user_password_reset_tokens_query.all()
        ]
        for token_id in reset_token_ids:
            auth_utils.blacklist_token(token_id)

        # hash the new password and update the password field in user table
        hashed_password = password_utils.get_hash(reset.password)
        user_query.update({"password": hashed_password}, synchronize_session=False)

        # add an entry to password change history table
        add_password_change_history_entry = user_model.PasswordChangeHistory(
            user_id=user.id
        )
        db.add(add_password_change_history_entry)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing change password request",
        ) from exc

    return {"message": "Password change successful"}


@router.post("/{username}/password/change")
def change_password_update(
    username: str,
    old_password: str = Form(),
    new_password: str = Form(),
    confirm_new_password: str = Form(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    update = user_schema.UserPasswordChangeUpdate(
        old_password=old_password,
        new_password=new_password,
        confirm_new_password=confirm_new_password,
    )

    # get the user using username
    user_query = user_service.get_user_by_username_query(username, ["DEL"], db)

    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    if user.status in [
        "TBN",
        "PBN",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to process your request at this time. Please contact support for assistance.",
        )

    # check user identity
    if current_user.email != user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # check both old password and new password
    if update.old_password == update.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be same as Old Password",
        )

    # check old password
    old_password_check = password_utils.verify_password(
        update.old_password, user.password
    )
    if not old_password_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Old password invalid"
        )

    # check both newly entered passwords
    if update.new_password != update.confirm_new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del confirm_new_password

    try:
        # hash the new password and update the password field in user table
        hashed_password = password_utils.get_hash(update.new_password)
        user_query.update({"password": hashed_password}, synchronize_session=False)

        # add an entry to password change history table
        add_password_change_history_entry = user_model.PasswordChangeHistory(
            user_id=user.id
        )
        db.add(add_password_change_history_entry)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing change password request",
        ) from exc

    return {"message": "Password change successful"}


# follow/unfollow users
@router.post("/follow")
def follow_user(
    followed_user: user_schema.UserFollow,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    # get the user to be followed
    user_followed = user_service.get_user_by_username(
        followed_user.username,
        ["PBN", "DEL"],
        db,
    )
    if not user_followed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User to be followed not found",
        )

    if user_followed.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile to be followed not found",
        )

    # get follower user
    follower_user = user_service.get_user_by_email(
        current_user.email,
        ["PBN", "DEL"],
        db,
    )

    # user cannot follow/unfollow him/herself
    if followed_user.username == follower_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User cannot follow/unfollow itself",
        )

    # get followed user's followers
    following_usernames = [
        follower_association.follower.username
        for follower_association in user_followed.followers
    ]

    # follow a user
    if followed_user.action == "follow":
        # check if already follows the user
        if follower_user.username in following_usernames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You already are following {user_followed.username}",
            )

        # if user is private then send request orelse follow directly
        if user_followed.account_visibility == "PRV":  # type: ignore
            # check if follow request already sent
            check_request_sent = user_service.get_user_follow_association_entry_query(
                str(follower_user.id),
                str(user_followed.id),
                "PND",
                db,
            )
            if check_request_sent.first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Follow request is already sent",
                )

            follow_request = user_model.UserFollowAssociation(
                status="PND",
                follower=follower_user,
                followed=user_followed,
            )
            db.add(follow_request)
            db.commit()

            return {"message": f"Follow request sent to {followed_user.username}"}
        else:
            follow = user_model.UserFollowAssociation(
                status="ACP",
                follower=follower_user,
                followed=user_followed,
            )
            db.add(follow)
            db.commit()

            print(user_followed.followers)
            return {"message": f"Following {followed_user.username}"}

    # unfollow a user
    elif followed_user.action == "unfollow":
        # check if follows the user
        if follower_user.username not in following_usernames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You are not following {user_followed.username}",
            )
        # get user follow entry query
        user_follow_query = user_service.get_user_follow_association_entry_query(
            str(follower_user.id),
            str(user_followed.id),
            "ACP",
            db,
        )
        if not user_follow_query.first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User follow entry not found",
            )

        # update the status to unfollowed
        user_follow_query.update(
            {"status": "UNF"},
            synchronize_session=False,
        )
        db.commit()

        following_usernames = [
            follower_association.follower.username
            for follower_association in user_followed.followers
        ]
        print(following_usernames)
        return {"message": f"Unfollowed {followed_user.username}"}


# accept/reject follow request
@router.put("/follow/requests/{username}")
def manage_follow_request(
    username: str,
    follow_request: user_schema.UserFollowRequest,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    # check for user using username
    follower_user = user_service.get_user_by_username(
        username,
        ["PBN", "DEL"],
        db,
    )
    if not follower_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follower user not found"
        )
    if follower_user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follower user profile not found",
        )

    # get current user object
    user = user_service.get_user_by_email(
        current_user.email,
        ["PBN", "DEL"],
        db,
    )

    # check for user follow entry with status pending
    user_follow_query = user_service.get_user_follow_association_entry_query(
        str(follower_user.id),
        str(user.id),
        "PND",
        db,
    )
    if not user_follow_query.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User follow entry not found"
        )

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
        db.commit()

        return {"message": f"Following {user.username}"}

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
        db.commit()

        return {"message": f"Rejected the request to follow {user.username}"}


# get all followers/following of a user
@router.get(
    "/{username}/follow",
    response_model=list[user_schema.UserFollowersFollowingResponse],
)
def get_user_followers_following(
    username: str,
    request_info: user_schema.UserFollowersFollowing,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
    # can't use Depends(auth_utils.check_access_role(role="user")) because Depends doesn't support extra params directly
    # hence we have a custom dependency class which will set the role param and call the get_current_user function
):
    # get user from username
    user = user_service.get_user_by_username(
        username,
        ["PBN", "DEL"],
        db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        str(current_user.email),
        ["PBN", "DEL"],
        db,
    )

    # get details only if owner or public account or follower
    follower_check = user_service.check_user_follower_or_not(
        str(curr_auth_user.id), str(user.id), db
    )

    if (username != curr_auth_user.username) and (user.account_visibility == "PRV" and not follower_check):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # getting count of followers and following, testing
    print(len(curr_auth_user.followers))
    print(len(curr_auth_user.following))

    # check the fetch
    followers_list = []
    following_list = []
    curr_auth_user_following_usernames = [
        following_association.followed.username
        for following_association in curr_auth_user.following
    ]
    if request_info.fetch == "followers":
        user_followers = [
            follower_association.follower for follower_association in user.followers
        ]
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

    elif request_info.fetch == "following":
        user_following = [
            following_association.followed for following_association in user.following
        ]
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing request"
        )


# get all follow requests of a user
@router.get(
    "/{username}/follow/requests",
    response_model=list[user_schema.UserGetFollowRequestsResponse],
)
def get_follow_requests(
    username: str,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    # get user from username
    user = user_service.get_user_by_username(
        username,
        ["PBN", "DEL"],
        db,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        current_user.email,
        ["PBN", "DEL"],
        db,
    )

    # check user identity
    if username != curr_auth_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # get all follow requests
    user_follow_requests_entries = user_service.get_user_follow_requests(
        str(user.id), "PND", db
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
                    "RSF",
                    "RSP",
                    "TBN",
                ]
            ),
        )
        .all()
    )
    print(requests_users)
    return requests_users


# remove a follower
@router.put("/follow/remove/{username}")
def remove_follower(
    username: str,
    user_request: user_schema.UserRemoveFollower,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    # get user from username
    follower_user = user_service.get_user_by_username(username, ["PBN", "DEL"], db)
    if not follower_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follower user not found"
        )

    if follower_user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follower user profile not found",
        )

    # get request user
    user = user_service.get_user_by_username(user_request.username, ["PBN", "DEL"], db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        str(current_user.email), ["PBN", "DEL"], db
    )

    # check user identity
    if user_request.username != curr_auth_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # get the user follow association entry
    user_follow_entry_query = user_service.get_user_follow_association_entry_query(
        follower_user.id, curr_auth_user.id, "ACP", db
    )
    user_follow_entry = user_follow_entry_query.first()
    if not user_follow_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User follow entry not found"
        )

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

    return {
        "message": f"{follower_user.username} has been removed from your followers successfully"
    }


# update username
@router.post("/{username}/username/change")
def username_change(
    username: str,
    new_username: str = Form(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    update = user_schema.UserUsernameChange(new_username=new_username)

    # get user from username
    user_query = user_service.get_user_by_username_query(
        username,
        ["PBN", "DEL"],
        db,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # check user identity
    if current_user.email != user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # check if new username matches old username
    if update.new_username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New username cannot be same as old username",
        )

    # check if new username already taken
    username_exists = user_service.check_username_exists(update.new_username, db)
    if username_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username {update.new_username} is already taken",
        )

    try:
        # update username
        user_query.update({"username": update.new_username}, synchronize_session=False)

        # add entry to username change history table
        add_username_change_history_entry = user_model.UsernameChangeHistory(
            previous_username=username, user_id=user.id
        )
        db.add(add_username_change_history_entry)

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing username change request",
        ) from exc

    return {"message": "Username change successful"}


# deactivate/soft-delete the user account
@router.patch("/{username}/{action}")
def deactivate_or_soft_delete_user(
    username: str,
    action: str,
    background_tasks: BackgroundTasks,
    password: str = Form(None),
    hide_interactions: bool = Form(),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    # check for password in the request
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Password required"
        )

    # create object
    deactivate_delete_request = user_schema.UserDeactivationDeletion(
        password=password, hide_interactions=hide_interactions
    )

    # get user from username
    user_query = user_service.get_user_by_username_query(
        username,
        ["PBN", "DEL"],
        db,
    )
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    # check if password is right
    password_check = password_utils.verify_password(
        deactivate_delete_request.password, user.password
    )
    if not password_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        current_user.email,
        ["PBN", "DEL"],
        db,
    )

    # check user identity
    if username != curr_auth_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action",
        )

    # check action
    if action == "deactivate":
        # update status of the user
        if deactivate_delete_request.hide_interactions:
            user_query.update(
                {"status": "DAH"},
                synchronize_session=False,
            )
        else:
            user_query.update(
                {"status": "DAK"},
                synchronize_session=False,
            )

        db.commit()

        return {"message": "Your account has been deactivated successfully"}

    elif action == "delete":
        # send mail informing user about the account deletion, we will using mailtrap dummy server for testing
        try:
            email_subject = "Your VPKonnect account is scheduled for deletion"
            email_details = admin_schema.SendEmail(
                template="account_deletion_email.html",
                email=[user.email],
                body_info={"username": user.username},
            )
            email_utils.send_email(email_subject, email_details, background_tasks)

            # update status to pending_deletion_(hide/keep)
            if deactivate_delete_request.hide_interactions:
                user_query.update(
                    {"status": "PDH"},
                    synchronize_session=False,
                )
            else:
                user_query.update(
                    {"status": "PDK"},
                    synchronize_session=False,
                )
            db.commit()
        except Exception as exc:
            print(exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="There was an error in processing delete user request",
            ) from exc

        return {
            "message": f"Your account deletion request is accepted. {user.username} account will be deleted after a deactivation period of 30 days. An email for the same has been sent to {user.email}"
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error processing request"
        )


# # deactivate the user account
# @router.patch("/{username}/deactivate")
# def deactivate_user(
#     username: str,
#     password: str = Form(),
#     hide_interactions: bool = Form(),
#     db: Session = Depends(get_db),
#     current_user: auth_schema.AccessTokenPayload = Depends(
#         auth_utils.AccessRoleDependency(role="user")
#     ),
# ):
#     # check if password is entered or not
#     if not password:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Password required"
#         )

#     # create deactivation object
#     deactivate_request = user_schema.UserDeactivation(
#         password=password, hide_interactions=hide_interactions
#     )

#     # get user query object from username
#     user_query = user_service.get_user_by_username_query(username, ["PBN", "DEL"], db)
#     user = user_query.first()
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     if user.status in [
#         "DAH",
#         "DAK",
#         "PDH",
#         "PDK",
#     ]:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
#         )

#     # check if password is right
#     password_check = password_utils.verify_password(
#         deactivate_request.password, user.password
#     )
#     if not password_check:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
#         )

#     # check user identity
#     if username != user.username:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to perform requested action",
#         )

#     # update status of the user
#     if deactivate_request.hide_interactions:
#         user_query.update(
#             {"status": "DAH"},
#             synchronize_session=False,
#         )
#     else:
#         user_query.update(
#             {"status": "DAK"},
#             synchronize_session=False,
#         )

#     db.commit()

#     return {"message": "Your account has been deactivated successfully"}


# report an item
@router.post("/item/report")
def report_item(
    reported_item: user_schema.UserContentReport,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="user")
    ),
):
    # check if item is there or not
    if reported_item.item_type == "post":
        post = post_service.get_a_post(str(reported_item.item_id), ["DRF", "DEL"], db)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )
        if post.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Post already banned",
            )
    elif reported_item.item_type == "comment":
        comment = comment_service.get_a_comment(str(reported_item.item_id), ["DEL"], db)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if comment.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Comment already banned",
            )

    # get the reporter and reported user
    reporter_user = user_service.get_user_by_email(
        str(current_user.email), ["PBN", "DEL"], db
    )
    reported_user = user_service.get_user_by_username(
        reported_item.username, ["DEL", "PBN"], db
    )
    if not reported_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if reported_user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
    ]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )

    report_reason_user = None
    if reported_item.item_type == "account":
        reported_item.item_id = reported_user.id

        # if impersonation report where username is specified
        if reported_item.reason_username:
            report_reason_user = user_service.get_user_by_username(
                reported_item.reason_username, ["PBN", "DEL"], db
            )
            if not report_reason_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Original user not found",
                )
            if report_reason_user.status in [
                "DAH",
                "DAK",
                "PDH",
                "PDK",
            ]:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Original user profile not found",
                )

    # user cannot report his/her own item
    if reporter_user.username == reported_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User cannot report own content",
        )

    # check table if report exists of same user for same item and same reason
    same_user_report = user_service.check_if_same_report_exists(
        reporter_user.id, str(reported_item.item_id), reported_item.reason, db
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
    db.add(user_report)
    db.commit()

    return {
        "message": f"This {reported_item.item_type} has been reported anonymously and will be handled by content moderator."
    }
