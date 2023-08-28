from sqlalchemy.orm import Session

from app.models import user as user_models


def get_user_by_username(username: str, db_session: Session):
    return (
        db_session.query(user_models.User)
        .filter(user_models.User.username == username)  # type:ignore
        .first()
    )


def get_user_by_email(email: str, db_session: Session):
    return (
        db_session.query(user_models.User)
        .filter(user_models.User.email == email)
        .first()
    )


def check_username_exists(username: str, db_session: Session):
    return get_user_by_username(username, db_session)


def check_user_exists(email: str, db_session: Session):
    return get_user_by_email(email, db_session)
