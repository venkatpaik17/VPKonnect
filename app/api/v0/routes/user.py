import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pyfa_converter import FormDepends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import user as user_model
from app.schemas import user as user_schema
from app.services.user import check_user_exists, check_username_exists
from app.utils import image as image_utils
from app.utils import password

router = APIRouter(prefix="/users", tags=["Users"])


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
    # create a subfolder for user specific uploads, if folder exists get it.
    user_subfolder = image_utils.get_or_create_user_image_subfolder(request.username)

    # if there is image uploaded, create a subfolder for profile pics, if folder exists get it. Upload the image in this folder.
    if image:
        profile_subfolder = image_utils.get_or_create_user_profile_image_subfolder(
            user_subfolder
        )
        upload_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
        image_name = f"{request.username}_{upload_datetime}_{image.filename}"
        image_path = profile_subfolder / image_name
        with open(image_path, "wb+") as f:
            shutil.copyfileobj(image.file, f)

        add_user = user_model.User(**request.dict(), profile_picture=image_name)

    else:
        add_user = user_model.User(**request.dict())

    # store image directly in the DB
    # add_user = user_model.User(**request.dict(), profile_picture=image.file.read())

    db.add(add_user)
    db.commit()
    db.refresh(add_user)

    return add_user
