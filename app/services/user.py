from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models import admin as admin_model
from app.models import user as user_model


def get_user_by_username(
    username: str,
    status_not_in_list: list[str],
    db_session: Session,
    is_verified: bool = True,
):
    return get_user_by_username_query(
        username, status_not_in_list, db_session, is_verified
    ).first()


def get_user_by_username_query(
    username: str,
    status_not_in_list: list[str],
    db_session: Session,
    is_verified: bool = True,
):
    return db_session.query(user_model.User).filter(
        user_model.User.username == username,
        user_model.User.status.notin_(status_not_in_list),
        user_model.User.is_deleted == False,
        user_model.User.is_verified == is_verified,
    )


def get_user_by_email(
    email: str,
    status_not_in_list: list[str],
    db_session: Session,
    is_verified: bool | None = True,
):
    return get_user_by_email_query(
        email, status_not_in_list, db_session, is_verified
    ).first()


def get_user_by_email_query(
    email: str,
    status_not_in_list: list[str],
    db_session: Session,
    is_verified: bool | None = True,
):
    return db_session.query(user_model.User).filter(
        user_model.User.email == email,
        user_model.User.status.notin_(status_not_in_list),
        user_model.User.is_deleted == False,
        user_model.User.is_verified == is_verified if is_verified else True,
    )


def check_username_exists(username: str, db_session: Session, is_verified: bool = True):
    return get_user_by_username_query(
        username, ["PDB", "PDI", "DEL"], db_session, is_verified
    ).first()


def check_user_exists(email: str, db_session: Session, is_verified: bool = True):
    return get_user_by_email_query(
        email, ["PDB", "PDI", "DEL"], db_session, is_verified
    ).first()


def get_user_by_id_query(
    user_id: str, status_not_in_list: list[str] | None, db_session: Session
):
    return db_session.query(user_model.User).filter(
        user_model.User.id == user_id,
        (
            user_model.User.status.notin_(status_not_in_list)
            if status_not_in_list
            else True
        ),
        user_model.User.is_deleted == False,
        user_model.User.is_verified == True,
    )


def get_user_by_id(
    user_id: str, status_not_in_list: list[str] | None, db_session: Session
):
    return get_user_by_id_query(user_id, status_not_in_list, db_session).first()


def get_all_users_admin(
    status_in_list: list[str] | None,
    db_session: Session,
    sort: str | None,
):
    query = db_session.query(user_model.User).filter(
        (user_model.User.status.in_(status_in_list)) if status_in_list else True,
    )

    if sort == "asc":
        return query.order_by(user_model.User.created_at.asc()).all()

    return query.order_by(user_model.User.created_at.desc()).all()


# get all users by id
def get_all_users_by_id(
    user_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return (
        db_session.query(user_model.User)
        .filter(
            user_model.User.id.in_(user_id_list),
            user_model.User.status.in_(status_in_list),
            user_model.User.is_verified == True,
            user_model.User.is_deleted == False,
        )
        .all()
    )


# get user by username and email
def get_user_by_username_email(
    username: str, email: str, status_in_list: list[str], db_session: Session
):
    return (
        db_session.query(user_model.User)
        .filter(
            user_model.User.username == username,
            user_model.User.email == email,
            user_model.User.status.in_(status_in_list),
            user_model.User.is_verified == True,
            user_model.User.is_deleted == False,
        )
        .first()
    )


# get user by status
def get_user_by_status(status_in_list: list[str], db_session: Session):
    return db_session.query(user_model.User).filter(
        user_model.User.status.in_(status_in_list),
        user_model.User.is_verified == True,
        user_model.User.is_deleted == False,
    )


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
        user_model.UserSession.is_deleted == False,
    )


# get the query for all user session entries using user id
def get_user_session_entries_query_by_user_id(
    user_id: str, is_active: bool, db_session: Session
):
    return db_session.query(user_model.UserSession).filter(
        user_model.UserSession.user_id == user_id,
        user_model.UserSession.is_active == is_active,
        user_model.UserSession.is_deleted == False,
    )


# get user follow entry
def get_user_follow_association_entry_query(
    follower_id: str, followed_id: str, status: str, db_session: Session
):
    return db_session.query(user_model.UserFollowAssociation).filter(
        user_model.UserFollowAssociation.follower_user_id == follower_id,
        user_model.UserFollowAssociation.followed_user_id == followed_id,
        user_model.UserFollowAssociation.status == status,
        user_model.UserFollowAssociation.is_deleted == False,
    )


# check if follower or not
def check_user_follower_or_not(follower_id: str, followed_id: str, db_session: Session):
    return get_user_follow_association_entry_query(
        follower_id, followed_id, status="ACP", db_session=db_session
    ).first()


# get user follow requests
def get_user_follow_requests(followed_id: str, status: str, db_session: Session):
    return (
        db_session.query(user_model.UserFollowAssociation)
        .filter(
            user_model.UserFollowAssociation.followed_user_id == followed_id,
            user_model.UserFollowAssociation.status == status,
            user_model.UserFollowAssociation.is_deleted == False,
        )
        .all()
    )


# get users whose deactivation period for scheduled delete is done
def check_deactivation_expiration_for_scheduled_delete(db_session: Session):
    # get latest entries of each user
    subq = (
        db_session.query(
            user_model.UserAccountHistory.user_id,
            func.max(user_model.UserAccountHistory.created_at).label(
                "latest_created_at"
            ),
        )
        .group_by(user_model.UserAccountHistory.user_id)
        .subquery()
    )

    # inner join with the table to get the required user account history entries
    return (
        db_session.query(user_model.UserAccountHistory)
        .join(
            subq,
            and_(
                user_model.UserAccountHistory.user_id == subq.c.user_id,
                user_model.UserAccountHistory.created_at == subq.c.latest_created_at,
            ),
        )
        .filter(
            user_model.UserAccountHistory.account_detail_type == "Account",
            user_model.UserAccountHistory.event_type.in_(["DDS", "BDS", "IDS"]),
            func.now()
            >= (user_model.UserAccountHistory.created_at + timedelta(days=30)),
            user_model.UserAccountHistory.is_deleted == False,
        )
        .all()
    )


# # get users whose community guidelines violation period is over and specific action needs to be taken
# def check_violation_period_expiration_query(
#     status_list: list[str], time_period: int, db_session: Session
# ):
#     return db_session.query(user_model.User).filter(
#         user_model.User.status.in_(status_list),
#         func.now() > user_model.User.updated_at + timedelta(hours=time_period),
#     )


# get report entry from usercontentreportdetail table
def check_if_same_report_exists(
    user_id: str, content_id: str, report_reason: str, db_session: Session
):
    return (
        db_session.query(admin_model.UserContentReportDetail)
        .filter(
            admin_model.UserContentReportDetail.reporter_user_id == user_id,
            admin_model.UserContentReportDetail.reported_item_id == content_id,
            admin_model.UserContentReportDetail.report_reason == report_reason,
            admin_model.UserContentReportDetail.is_deleted == False,
        )
        .first()
    )


# get user account history entry for a user
def get_user_account_history_entry(
    user_id: UUID, account_detail_type: str, event_type: str, db_session: Session
):
    return (
        db_session.query(user_model.UserAccountHistory)
        .filter(
            user_model.UserAccountHistory.user_id == user_id,
            user_model.UserAccountHistory.account_detail_type == account_detail_type,
            user_model.UserAccountHistory.event_type == event_type,
            user_model.UserAccountHistory.is_deleted == False,
        )
        .first()
    )


def count_followers(user_id: UUID, status: str, db_session: Session):
    return (
        db_session.query(func.count(user_model.UserFollowAssociation.id))
        .filter(
            user_model.UserFollowAssociation.followed_user_id == user_id,
            user_model.UserFollowAssociation.status == status,
            user_model.UserFollowAssociation.is_deleted == False,
        )
        .scalar()
    )


def count_following(user_id: UUID, status: str, db_session: Session):
    return (
        db_session.query(func.count(user_model.UserFollowAssociation.id))
        .filter(
            user_model.UserFollowAssociation.follower_user_id == user_id,
            user_model.UserFollowAssociation.status == status,
            user_model.UserFollowAssociation.is_deleted == False,
        )
        .scalar()
    )


# U4 followed by. users (U2, U3) followed by you (U1), following another user (U4)
def user_followed_by(current_user_id: UUID, profile_user_id: UUID, db_session: Session):
    user_follow_assoc_1 = aliased(user_model.UserFollowAssociation, name="ufa1")
    user_follow_assoc_2 = aliased(user_model.UserFollowAssociation, name="ufa2")
    return (
        db_session.query(user_follow_assoc_1)
        .join(
            user_follow_assoc_2,
            user_follow_assoc_1.followed_user_id
            == user_follow_assoc_2.follower_user_id,
            isouter=True,
        )
        .filter(
            user_follow_assoc_1.follower_user_id == current_user_id,
            user_follow_assoc_2.followed_user_id == profile_user_id,
            user_follow_assoc_1.status == "ACP",
            user_follow_assoc_2.status == "ACP",
            user_follow_assoc_1.is_deleted == False,
            user_follow_assoc_2.is_deleted == False,
        )
        .all()
    )


# get user following ids
def get_user_following_ids(user_id: UUID, db_session: Session):
    stmt = select(user_model.UserFollowAssociation.followed_user_id).filter(
        user_model.UserFollowAssociation.follower_user_id == user_id,
        user_model.UserFollowAssociation.status == "ACP",
        user_model.UserFollowAssociation.is_deleted == False,
    )

    return db_session.execute(stmt).scalars().all()
