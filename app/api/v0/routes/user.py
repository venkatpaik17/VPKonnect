import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pyfa_converter import FormDepends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import user as user_model
from app.schemas import user as user_schema
from app.services.user import check_user_exists, check_username_exists
from app.utils import image as image_utils
from app.utils import password

router = APIRouter(prefix="/users", tags=["Users"])

MAX_SIZE = 5 * 1024 * 1024


@router.post("/register", response_model=user_schema.UserRegisterResponse)
def create_user(
    request: user_schema.UserRegister = FormDepends(user_schema.UserRegister),  # type: ignore
    db: Session = Depends(get_db),
    image: UploadFile | None = None,
):
    username_check = check_username_exists(request.username, db)
    if username_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username {request.username} is already taken",
        )
    user_check = check_user_exists(request.email, db)
    if user_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{request.email} already exists in the system",
        )
    hashed_password = password.get_hash(request.password)
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
