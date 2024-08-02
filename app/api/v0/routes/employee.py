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

    # create a subfolder for user specific uploads, if folder exists get it.
    employee_subfolder = image_utils.get_or_create_entity_image_subfolder(
        entity="employee", repr_id=str(emp_id)
    )

    # create a subfolder for profile images, if folder exists get it.
    profile_subfolder = image_utils.get_or_create_entity_profile_image_subfolder(
        entity_subfolder=employee_subfolder
    )

    add_employee = employee_model.Employee(
        **request.dict(), emp_id=emp_id, supervisor_id=supervisor_id
    )

    image_path = None
    if image:
        # image validation and handling
        image_name, image_path = image_utils.handle_image_operations(
            username=emp_id, target_folder=profile_subfolder, image=image
        )

        add_employee = employee_model.Employee(
            **request.dict(),
            emp_id=emp_id,
            profile_picture=image_name,
            supervisor_id=supervisor_id,
        )

    try:
        db.add(add_employee)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        if image and image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering employee",
        ) from exc

    # store image directly in the DB
    # add_user = user_model.User(**request.dict(), profile_picture=image.file.read())

    # db.refresh(add_employee)

    return add_employee
