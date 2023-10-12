from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import user as user_model
from app.utils import enum as enum_utils


def get_user_by_username(
    username: str, status_not_in_list: list[str], db_session: Session
):
    return get_user_by_username_query(username, status_not_in_list, db_session).first()


def get_user_by_username_query(
    username: str, status_not_in_list: list[str], db_session: Session
):
    return db_session.query(user_model.User).filter(
        user_model.User.username == username,
        user_model.User.status.notin_(status_not_in_list),
    )


def get_user_by_email(email: str, status_not_in_list: list[str], db_session: Session):
    return get_user_by_email_query(email, status_not_in_list, db_session).first()


def get_user_by_email_query(
    email: str, status_not_in_list: list[str], db_session: Session
):
    return db_session.query(user_model.User).filter(
        user_model.User.email == email,
        user_model.User.status.notin_(status_not_in_list),
    )


def check_username_exists(username: str, db_session: Session):
    return get_user_by_username_query(
        username, [enum_utils.UserStatusEnum.DELETED], db_session
    ).first()


def check_user_exists(email: str, db_session: Session):
    return get_user_by_email_query(
        email, [enum_utils.UserStatusEnum.DELETED], db_session
    ).first()


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


# get users whose deactivation period is done
def check_deactivation_expiration_query(db_session: Session):
    return db_session.query(user_model.User).filter(
        user_model.User.status.in_(
            [
                enum_utils.UserStatusEnum.PENDING_DELETE_HIDE,
                enum_utils.UserStatusEnum.PENDING_DELETE_KEEP,
            ]
        ),
        func.now() > user_model.User.updated_at + timedelta(days=30),
    )
