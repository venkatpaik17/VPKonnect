import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pyfa_converter import FormDepends
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import employee as employee_model
from app.schemas import employee as employee_schema
from app.services import employee as employee_service
from app.utils import image as image_utils
from app.utils import password as password_utils

router = APIRouter(prefix=settings.api_prefix + "/employees", tags=["Employees"])

MAX_SIZE = 5 * 1024 * 1024


@router.post(
    "/register",
    response_model=employee_schema.EmployeeRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    request: employee_schema.EmployeeRegister = FormDepends(
        employee_schema.EmployeeRegister
    ),  # type: ignore
    supervisor: str = Form(None),
    db: Session = Depends(get_db),
    image: UploadFile | None = None,
):
    # check both entered passwords are same
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del request.confirm_password

    # check if employee already exists
    employee_check = employee_service.get_employee_by_work_email(request.work_email, db)
    if employee_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{request.work_email} already exists in the system",
        )

    hashed_password = password_utils.get_hash(request.password)
    request.password = hashed_password

    # generate emp_id
    emp_id = db.query(
        func.generate_employee_id(
            request.first_name, request.last_name, request.join_date
        )
    ).scalar()

    # get the supervisor id from supervisor emp_id
    supervisor_id = None
    if supervisor:
        supervisor_id = employee_service.get_supervisor_id_from_supervisor_emp_id(
            supervisor, db
        )
        if not supervisor_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supervisor not found"
            )

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
            image_name = f"{emp_id}_{upload_datetime}_{image.filename}"

            add_employee = employee_model.Employee(**request.dict(), emp_id=emp_id, profile_picture=image_name, supervisor_id=supervisor_id)  # type: ignore
            db.add(add_employee)
            db.flush()

            # create a subfolder for user specific uploads, if folder exists get it.
            employee_subfolder = image_utils.get_or_create_entity_image_subfolder(
                "employee", str(add_employee.emp_id)
            )

            # create a subfolder for profile images, if folder exists get it.
            profile_subfolder = (
                image_utils.get_or_create_entity_profile_image_subfolder(
                    employee_subfolder
                )
            )

            image_path = profile_subfolder / image_name

            with open(image_path, "wb+") as f:
                shutil.copyfileobj(image.file, f)

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registering user",
            ) from exc
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error registering user",
            ) from exc

    else:
        add_employee = employee_model.Employee(
            **request.dict(), emp_id=emp_id, supervisor_id=supervisor_id
        )
        db.add(add_employee)
        db.commit()

        # store image directly in the DB
        # add_user = user_model.User(**request.dict(), profile_picture=image.file.read())

    db.refresh(add_employee)

    return add_employee
