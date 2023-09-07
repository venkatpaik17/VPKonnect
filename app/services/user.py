from sqlalchemy.orm import Session

from app.models import user as user_model


def get_user_by_username(username: str, db_session: Session):
    return (
        db_session.query(user_model.User)
        .filter(user_model.User.username == username)  # type:ignore
        .first()
    )


def get_user_by_email(email: str, db_session: Session):
    return (
        db_session.query(user_model.User).filter(user_model.User.email == email).first()
    )


def check_username_exists(username: str, db_session: Session):
    return get_user_by_username(username, db_session)


def check_user_exists(email: str, db_session: Session):
    return get_user_by_email(email, db_session)


# get the query for single user session entry
def get_user_session_one_entry_query(
    user_id: str, device_info: str, db_session: Session
):
    return db_session.query(user_model.UserSession).filter(
        user_model.UserSession.user_id == user_id,
        user_model.UserSession.device_info == device_info,
    )


# get the query for all user session entries using user id
def get_user_session_entries_query_by_user_id(user_id: str, db_session: Session):
    return db_session.query(user_model.UserSession).filter(
        user_model.UserSession.user_id == user_id
    )
