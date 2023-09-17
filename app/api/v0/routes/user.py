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
from pyfa_converter import FormDepends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import auth as auth_model
from app.models import user as user_model
from app.schemas import auth as auth_schema
from app.schemas import user as user_schema
from app.services import auth as auth_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import email as email_utils
from app.utils import image as image_utils
from app.utils import password as password_utils

router = APIRouter(prefix="/users", tags=["Users"])

MAX_SIZE = 5 * 1024 * 1024


@router.post("/register", response_model=user_schema.UserRegisterResponse)
def create_user(
    request: user_schema.UserRegister = FormDepends(user_schema.UserRegister),  # type: ignore
    db: Session = Depends(get_db),
    image: UploadFile | None = None,
):
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

            add_user = user_model.User(**request.dict(), profile_picture=image_name)
            db.add(add_user)
            db.flush()

            # create a subfolder for user specific uploads, if folder exists get it.
            user_subfolder = image_utils.get_or_create_user_image_subfolder(
                str(add_user.id)
            )

            # create a subfolder for profile images, if folder exists get it.
            profile_subfolder = image_utils.get_or_create_user_profile_image_subfolder(
                user_subfolder
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

    return add_user


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
    user = user_service.get_user_by_email(reset_user.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # generate a token
    claims = {"sub": user.email, "role": user.type}
    reset_token, reset_token_id = auth_utils.create_reset_token(claims)

    # generate reset link
    reset_link = f"https://vpkonnect.in/accounts/password/change/?token={reset_token}"

    # send mail with reset link if user is valid, we will using mailtrap dummy server for testing
    try:
        email_utils.send_email(
            user.username, reset_user.email, reset_link, background_tasks
        )
    except Exception as exc:
        auth_utils.blacklist_token(reset_token)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error in sending email",
        ) from exc

    # add the token id to user password reset token table
    add_reset_token_id = auth_model.UserPasswordResetToken(
        reset_token_id=reset_token_id, user_id=user.id
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

    # checklist token blacklist
    reset_token_blacklist_check = auth_utils.is_token_blacklisted(token_claims.token_id)
    if reset_token_blacklist_check:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Paswword reset failed, Token invalid/revoked",
        )

    # get the user
    user_query = user_service.get_user_by_email_query(token_claims.email, db)
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # get query to fetch all reset token ids related to the user
    user_password_reset_tokens_query = (
        auth_service.get_user_password_reset_tokens_query(str(user.id), db)
    )

    # check if token id of token got in form request exists
    token_id_check = user_password_reset_tokens_query.filter(
        auth_model.UserPasswordResetToken.reset_token_id == token_claims.token_id,
        auth_model.UserPasswordResetToken.is_deleted == False,
    ).first()
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
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    update = user_schema.UserPasswordChangeUpdate(
        old_password=old_password,
        new_password=new_password,
        confirm_new_password=confirm_new_password,
    )

    # get the user using username
    user_query = user_service.get_user_by_username_query(username, db)
    user = user_query.first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Old password invalid"
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
