from logging import Logger

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
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
from app.utils import log as log_utils
from app.utils import password as password_utils

router = APIRouter(prefix=settings.api_prefix + "/employees", tags=["Employees"])

MAX_SIZE = settings.image_max_size


@router.post(
    "/register",
    response_model=employee_schema.EmployeeRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    request: employee_schema.EmployeeRegister = FormDepends(
        employee_schema.EmployeeRegister
    ),  # type: ignore
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    image: UploadFile | None = None,
):
    # check both entered passwords are same
    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
        )

    del request.confirm_password

    # check if employee already exists
    employee_check = employee_service.get_employee_by_work_email(
        request.work_email, ["TER"], db
    )
    if employee_check:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{request.work_email} already exists in the system",
        )

    hashed_password = password_utils.get_hash(password=request.password)
    request.password = hashed_password

    # generate emp_id
    emp_id = db.query(
        func.generate_employee_id(
            request.first_name, request.last_name, request.join_date
        )
    ).scalar()

    # get the supervisor id from supervisor emp_id
    supervisor_id = None
    if request.supervisor:
        supervisor_id = employee_service.get_supervisor_id_from_supervisor_emp_id(
            supervisor_emp_id=request.supervisor, db_session=db
        )
        if not supervisor_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Supervisor not found"
            )

    add_employee = employee_model.Employee(
        **request.dict(), emp_id=emp_id, supervisor_id=supervisor_id
    )

    # create a subfolder for added employee specific uploads, if folder exists get it.
    employee_subfolder = image_utils.get_or_create_entity_image_subfolder(
        entity="employee", repr_id=str(emp_id), logger=logger
    )

    # create a subfolder for profile images, if folder exists get it.
    profile_subfolder = image_utils.get_or_create_entity_profile_image_subfolder(
        entity_subfolder=employee_subfolder, logger=logger
    )

    image_path = None
    try:
        if image:
            # image validation and handling
            image_name = image_utils.validate_image_generate_name(
                username=emp_id, image=image, logger=logger
            )

            add_employee.profile_picture = image_name

            image_path = profile_subfolder / image_name

            # write image to target
            image_utils.write_image(
                image=image,
                image_path=image_path,
                logger=logger,
            )

        db.add(add_employee)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        image_utils.remove_folder(path=employee_subfolder)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering employee",
        ) from exc
    except HTTPException as exc:
        image_utils.remove_folder(path=employee_subfolder)
        raise exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        image_utils.remove_folder(path=employee_subfolder)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return add_employee
