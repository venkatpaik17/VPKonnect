from calendar import month
from datetime import timedelta

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.config.app import settings
from app.models import auth as auth_model
from app.models import user as user_model


# get the entry with specific refresh token id and active status
def check_refresh_token_id_in_user_auth_track(
    token_id: str, status: str, db_session: Session
):
    return get_auth_track_entry_by_token_id_query(token_id, status, db_session).first()


# get the user auth track entry using user id and device info
def get_all_user_auth_track_entry_by_user_id_device_info(
    user_id: str, device_info: str, status: str, db_session: Session
):
    return (
        db_session.query(auth_model.UserAuthTrack)
        .filter(
            auth_model.UserAuthTrack.user_id == user_id,
            auth_model.UserAuthTrack.device_info == device_info,
            auth_model.UserAuthTrack.status == status,
            auth_model.UserAuthTrack.is_deleted == False,
        )
        .first()
    )


# get the query for user auth track entry using token id
def get_auth_track_entry_by_token_id_query(
    token_id: str, status: str, db_session: Session
):
    return db_session.query(auth_model.UserAuthTrack).filter(
        auth_model.UserAuthTrack.refresh_token_id == token_id,
        auth_model.UserAuthTrack.status == status,
        auth_model.UserAuthTrack.is_deleted == False,
    )


def get_all_user_auth_track_entries_by_user_id(
    user_id: str, status: str, db_session: Session
):
    return (
        db_session.query(auth_model.UserAuthTrack)
        .filter(
            auth_model.UserAuthTrack.user_id == user_id,
            auth_model.UserAuthTrack.status == status,
            auth_model.UserAuthTrack.is_deleted == False,
        )
        .all()
    )


# get the query for fetching all codes/tokens of a user
def get_user_verification_codes_tokens_query(
    user_id: str, _type: str, db_session: Session
):
    return db_session.query(auth_model.UserVerificationCodeToken).filter(
        auth_model.UserVerificationCodeToken.user_id == user_id,
        auth_model.UserVerificationCodeToken.type == _type,
    )


# get the query for employee auth track entry
def get_employee_auth_track_entry_by_token_id_query(
    token_id: str, status: str, db_session: Session
):
    return db_session.query(auth_model.EmployeeAuthTrack).filter(
        auth_model.EmployeeAuthTrack.refresh_token_id == token_id,
        auth_model.EmployeeAuthTrack.status == status,
        auth_model.EmployeeAuthTrack.is_deleted == False,
    )


def check_refresh_token_id_in_employee_auth_track(
    token_id: str, status: str, db_session: Session
):
    return get_employee_auth_track_entry_by_token_id_query(
        token_id, status, db_session
    ).first()


# get all employee auth track entries using employee id
def get_all_employee_auth_track_entries_by_employee_id(
    employee_id: str, status: str, db_session: Session
):
    return (
        db_session.query(auth_model.EmployeeAuthTrack)
        .filter(
            auth_model.EmployeeAuthTrack.employee_id == employee_id,
            auth_model.EmployeeAuthTrack.status == status,
            auth_model.EmployeeAuthTrack.is_deleted == False,
        )
        .all()
    )


def user_auth_track_user_inactivity_delete(db_session: Session):
    # join user and user_auth_track to get the latest entry in the past and compare it with inactive_delete_after to see if it is inactive for specified time to be deleted
    # subquery to get latest entry for each user
    latest_entry_subq = (
        db_session.query(
            auth_model.UserAuthTrack.user_id,
            func.max(auth_model.UserAuthTrack.created_at).label("latest_created_at"),
        )
        .group_by(auth_model.UserAuthTrack.user_id)
        .subquery()
    )

    # join user, user auth track and subquery with filters
    return (
        db_session.query(user_model.User)
        .join(
            auth_model.UserAuthTrack,
            auth_model.UserAuthTrack.user_id == user_model.User.id,
        )
        .join(
            latest_entry_subq,
            and_(
                auth_model.UserAuthTrack.user_id == latest_entry_subq.c.user_id,
                auth_model.UserAuthTrack.created_at
                == latest_entry_subq.c.latest_created_at,
            ),
        )
        .filter(
            user_model.User.status.in_(["INA"]),
            user_model.User.is_deleted == False,
            user_model.User.is_verified == True,
            auth_model.UserAuthTrack.status.in_(["ACT", "INV"]),
            func.now()
            >= (
                auth_model.UserAuthTrack.created_at
                + (user_model.User.inactive_delete_after * timedelta(days=1))
                + timedelta(minutes=settings.refresh_token_expire_minutes)
            ),
            auth_model.UserAuthTrack.is_deleted == False,
        )
        .all()
    )


def user_auth_track_user_inactivity_inactive(db_session: Session):
    # join user and user_auth_track to get the latest entry in the past
    # subquery to get latest entry for each user
    latest_entry_subq = (
        db_session.query(
            auth_model.UserAuthTrack.user_id,
            func.max(auth_model.UserAuthTrack.created_at).label("latest_created_at"),
        )
        .group_by(auth_model.UserAuthTrack.user_id)
        .subquery()
    )

    # join user, user auth track, subquery with filters
    return (
        db_session.query(auth_model.UserAuthTrack)
        .join(
            latest_entry_subq,
            and_(
                auth_model.UserAuthTrack.user_id == latest_entry_subq.c.user_id,
                auth_model.UserAuthTrack.created_at
                == latest_entry_subq.c.latest_created_at,
            ),
        )
        .filter(
            auth_model.UserAuthTrack.status.in_(["ACT", "INV"]),
            func.now()
            >= (
                auth_model.UserAuthTrack.created_at
                + timedelta(days=settings.user_inactivity_days)
                + timedelta(minutes=settings.refresh_token_expire_minutes)
            ),
            auth_model.UserAuthTrack.is_deleted == False,
        )
        .all()
    )
