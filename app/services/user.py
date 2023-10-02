from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import user as user_model


def get_user_by_username(username: str, db_session: Session):
    return (
        db_session.query(user_model.User)
        .filter(user_model.User.username == username)  # type:ignore
        .first()
    )


def get_user_by_username_query(username: str, db_session: Session):
    return db_session.query(user_model.User).filter(
        user_model.User.username == username
    )  # type:ignore


def get_user_by_email(email: str, db_session: Session):
    return (
        db_session.query(user_model.User).filter(user_model.User.email == email).first()
    )


def get_user_by_email_query(email: str, db_session: Session):
    return db_session.query(user_model.User).filter(user_model.User.email == email)


def check_username_exists(username: str, db_session: Session):
    return get_user_by_username(username, db_session)


def check_user_exists(email: str, db_session: Session):
    return get_user_by_email(email, db_session)


# get the query for single user session entry
def get_user_session_one_entry_query(
    user_id: str,
    device_info: str,
    is_active: bool,
    db_session: Session,
):
    return db_session.query(user_model.UserSession).filter(
        user_model.UserSession.user_id == user_id,
        user_model.UserSession.device_info == device_info,
        user_model.UserSession.is_active == is_active,
    )


# get the query for all user session entries using user id
def get_user_session_entries_query_by_user_id(
    user_id: str, is_active: bool, db_session: Session
):
    return db_session.query(user_model.UserSession).filter(
        user_model.UserSession.user_id == user_id,
        user_model.UserSession.is_active == is_active,
    )


# get user follow entry
def get_user_follow_association_entry_query(
    follower_id: str, followed_id: str, status: str, db_session: Session
):
    return db_session.query(user_model.UserFollowAssociation).filter(
        user_model.UserFollowAssociation.follower_user_id == follower_id,
        user_model.UserFollowAssociation.followed_user_id == followed_id,
        user_model.UserFollowAssociation.status == status,
    )


# check if follower or not
def check_user_follower_or_not(follower_id: str, followed_id: str, db_session: Session):
    return get_user_follow_association_entry_query(
        follower_id, followed_id, status="accepted", db_session=db_session
    ).first()


# get user follow requests
def get_user_follow_requests(followed_id: str, status: str, db_session: Session):
    return (
        db_session.query(user_model.UserFollowAssociation)
        .filter(
            user_model.UserFollowAssociation.followed_user_id == followed_id,
            user_model.UserFollowAssociation.status == status,
        )
        .all()
    )


def check_deactivation_expiration_query(db_session: Session):
    pattern = r"(_keep|_hide)$"
    return db_session.query(user_model.User).filter(
        user_model.User.status.op("~")(pattern),
        func.now() > user_model.User.updated_at + timedelta(days=30),
    )
