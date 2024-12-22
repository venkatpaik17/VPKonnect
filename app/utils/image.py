import shutil
from datetime import datetime
from logging import Logger
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.config.app import settings

image_folder = Path("images")
MAX_SIZE = settings.image_max_size


# def get_or_create_user_image_subfolder(username: str):
#     user_subfolder = image_folder / username
#     user_subfolder.mkdir(parents=True, exist_ok=True)

#     return user_subfolder


def get_or_create_entity_image_subfolder(entity: str, repr_id: str, logger: Logger):
    entity_subfolder = image_folder / entity / repr_id

    try:
        entity_subfolder.mkdir(parents=True, exist_ok=True)
    except FileNotFoundError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A required file or directory was not found on the server",
        ) from exc
    except OSError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing create folder request",
        ) from exc

    return entity_subfolder


def get_or_create_entity_profile_image_subfolder(
    entity_subfolder: Path, logger: Logger
):
    profile_subfolder = entity_subfolder / "profile"

    try:
        profile_subfolder.mkdir(parents=True, exist_ok=True)
    except FileNotFoundError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A required file or directory was not found on the server",
        ) from exc
    except OSError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing create folder request",
        ) from exc

    return profile_subfolder


def get_or_create_user_appeals_attachment_subfolder(
    user_subfolder: Path, logger: Logger
):
    appeals_subfolder = user_subfolder / "appeals"

    try:
        appeals_subfolder.mkdir(parents=True, exist_ok=True)
    except FileNotFoundError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A required file or directory was not found on the server",
        ) from exc
    except OSError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing create folder request",
        ) from exc

    return appeals_subfolder


def get_or_create_user_posts_image_subfolder(user_subfolder: Path, logger: Logger):
    posts_subfolder = user_subfolder / "posts"

    try:
        posts_subfolder.mkdir(parents=True, exist_ok=True)
    except FileNotFoundError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A required file or directory was not found on the server",
        ) from exc
    except OSError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing create folder request",
        ) from exc

    return posts_subfolder


def remove_image(path: Path):
    Path.unlink(path, missing_ok=True)


def remove_folder(path: Path):
    shutil.rmtree(path, ignore_errors=True)


def write_image(image: UploadFile, image_path: Path, logger: Logger):
    try:
        with open(image_path, "wb+") as f:
            shutil.copyfileobj(image.file, f)
    except FileNotFoundError as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File path not found",
        ) from exc
    except OSError as exc:
        if image_path.exists():
            remove_image(path=image_path)
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error writing image",
        ) from exc

    return image_path


def validate_image_generate_name(
    username: str,
    image: UploadFile,
    logger: Logger,
):
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
        # print(image_size)

        # if len(img_read) > MAX_SIZE: if image is read, we need to get the size using len()
        if image_size > MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image too large, you can upload upto 5 MiB",
            )

        # image name
        upload_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
        image_name = f"{username}_{upload_datetime}_{image.filename}"

    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format"
        ) from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing image",
        ) from exc

    return image_name


def handle_image_operations(
    username: str,
    target_folder: Path,
    image: UploadFile,
    logger: Logger,
):
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

        # image name and path
        upload_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
        image_name = f"{username}_{upload_datetime}_{image.filename}"

        image_path = target_folder / image_name

        with open(image_path, "wb+") as f:
            shutil.copyfileobj(image.file, f)

    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format"
        ) from exc
    except HTTPException as exc:
        raise exc
    except IOError as exc:
        remove_image(path=image_path)
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error writing image",
        ) from exc
    except Exception as exc:
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing image",
        ) from exc

    return image_name, image_path
