from sqlalchemy.orm import Session

from app.models import employee as employee_model


def get_employee_by_emp_id(
    emp_id: str, status_not_in_list: list[str], db_session: Session
):
    return (
        db_session.query(employee_model.Employee)
        .filter(
            employee_model.Employee.emp_id == emp_id,
            employee_model.Employee.status.notin_(status_not_in_list),
            employee_model.Employee.is_deleted == False,
        )
        .first()
    )


def get_employee_by_work_email(
    work_email: str, status_not_in_list: list[str], db_session: Session
):
    return (
        db_session.query(employee_model.Employee)
        .filter(
            employee_model.Employee.work_email == work_email,
            employee_model.Employee.status.notin_(status_not_in_list),
            employee_model.Employee.is_deleted == False,
        )
        .first()
    )


def get_supervisor_id_from_supervisor_emp_id(
    supervisor_emp_id: str, db_session: Session
):
    return (
        db_session.query(employee_model.Employee.id)
        .filter(
            employee_model.Employee.emp_id == supervisor_emp_id,
            employee_model.Employee.status.notin_(["SUP", "TER"]),
            employee_model.Employee.is_deleted == False,
        )
        .scalar()
    )


# get the query for single employee session entry
def get_employee_session_one_entry_query(
    employee_id: str,
    device_info: str,
    is_active: bool,
    db_session: Session,
):
    return db_session.query(employee_model.EmployeeSession).filter(
        employee_model.EmployeeSession.employee_id == employee_id,
        employee_model.EmployeeSession.device_info == device_info,
        employee_model.EmployeeSession.is_active == is_active,
        employee_model.EmployeeSession.is_deleted == False,
    )


# get the query for all employee session entries using id
def get_employee_session_entries_query_by_employee_id(
    employee_id: str, is_active: bool, db_session: Session
):
    return db_session.query(employee_model.EmployeeSession).filter(
        employee_model.EmployeeSession.employee_id == employee_id,
        employee_model.EmployeeSession.is_active == is_active,
        employee_model.EmployeeSession.is_deleted == False,
    )


def get_all_employees_admin(
    status: str | None,
    type_: str | None,
    designation_in_list: list[str] | None,
    sort: str | None,
    db_session: Session,
):
    query = db_session.query(employee_model.Employee).filter(
        employee_model.Employee.status == status if status else True,
        employee_model.Employee.type == type_ if type_ else True,
        (
            employee_model.Employee.designation.in_(designation_in_list)
            if designation_in_list
            else True
        ),
    )

    if sort == "asc":
        return query.order_by(employee_model.Employee.join_date.asc()).all()

    return query.order_by(employee_model.Employee.join_date.desc()).all()
