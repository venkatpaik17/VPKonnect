from sqlalchemy.orm import Session

from app.models import employee as employee_model


def get_employee_by_emp_id(emp_id: str, db_session: Session):
    return (
        db_session.query(employee_model.Employee)
        .filter(
            employee_model.Employee.emp_id == emp_id,
            employee_model.Employee.status.notin_(["TER"]),
        )
        .first()
    )


def get_employee_by_work_email(work_email: str, db_session: Session):
    return (
        db_session.query(employee_model.Employee)
        .filter(
            employee_model.Employee.work_email == work_email,
            employee_model.Employee.status.notin_(["TER"]),
        )
        .first()
    )


def get_supervisor_id_from_supervisor_emp_id(
    supervisor_emp_id: str, db_session: Session
):
    return (
        db_session.query(employee_model.Employee)
        .filter(employee_model.Employee.emp_id == supervisor_emp_id)
        .first()
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
    )


# get the query for all employee session entries using id
def get_employee_session_entries_query_by_employee_id(
    employee_id: str, is_active: bool, db_session: Session
):
    return db_session.query(employee_model.EmployeeSession).filter(
        employee_model.EmployeeSession.employee_id == employee_id,
        employee_model.EmployeeSession.is_active == is_active,
    )
