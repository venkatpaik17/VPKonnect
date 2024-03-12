from http.client import HTTPException

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import admin as admin_model
from app.models import user as user_model
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import user as user_service


def delete_user_after_deactivation_period_expiration(db: Session = next(get_db())):
    # get all delete schedule duration expiry entries
    scheduled_delete_entries = (
        user_service.check_deactivation_expiration_for_scheduled_delete(db_session=db)
    )

    if scheduled_delete_entries:
        # fetch user ids
        scheduled_delete_user_ids = [user.user_id for user in scheduled_delete_entries]

        # get the users
        users_to_be_deleted = user_service.get_all_users_by_id(
            user_id_list=scheduled_delete_user_ids,
            status_in_list=["PDK", "PDH"],
            db_session=db,
        )

        if users_to_be_deleted:
            try:
                for user in users_to_be_deleted:
                    user.status = "DEL"
                    user.is_deleted = True

                db.commit()
            except SQLAlchemyError as exc:
                db.rollback()
                print("SQL Error: ", exc)

    print("Delete Users. Job Done")


def remove_restriction_on_user_after_duration_expiration(db: Session = next(get_db())):
    remove_restrict_users_query = (
        admin_service.get_restricted_users_duration_expired_query(db_session=db)
    )
    remove_restrict_users = remove_restrict_users_query.all()
    if remove_restrict_users:
        try:
            # update is_active to False to all expired restrictions
            remove_restrict_users_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            # get the user ids
            remove_restrict_user_ids_report_ids = [
                (item.user_id, item.report_id) for item in remove_restrict_users
            ]

            # for every user id, check if there is any consecutive violation.
            # Since we have already updated is_active to False of the current active restrict/ban, we need to exclude that entry while getting next violation, so we use report_id in filter
            # if there is any, then enforce that violation i.e. update is_active to True, also if user current status is DAH/DAK/PDH/PDK/INA then don't update status, else update
            # if there is no consecutive violation then check current user status, if it is DAH/DAK/PDH/PDK/INA then don't update status, else update
            # there can be no consecutive violation for status already PBN
            for (
                restrict_user_id,
                restrict_report_id,
            ) in remove_restrict_user_ids_report_ids:
                # order_by is for get the rows in a specific order,it is read only, not for updating the rows
                # consecutive_violation_query = (
                #     db.query(admin_model.UserRestrictBanDetail)
                #     .filter(
                #         admin_model.UserRestrictBanDetail.user_id == restrict_user_id,
                #         admin_model.UserRestrictBanDetail.enforce_action_at
                #         < func.now(),
                #         admin_model.UserRestrictBanDetail.is_active == False,
                #         admin_model.UserRestrictBanDetail.is_deleted == False,
                #     )
                #     .order_by(admin_model.UserRestrictBanDetail.enforce_action_at.asc())
                # )

                # subquery to get the next nearest enforce_action_at which is greater than now(), scalar is used to directly fetch the value of single column value from the query
                subq_min_enforce_action_at = (
                    db.query(
                        func.min(admin_model.UserRestrictBanDetail.enforce_action_at)
                    )
                    .filter(
                        admin_model.UserRestrictBanDetail.user_id == restrict_user_id,
                        admin_model.UserRestrictBanDetail.report_id
                        != restrict_report_id,  # exclude the current deactivated restrict/ban entry
                        admin_model.UserRestrictBanDetail.enforce_action_at
                        <= func.now(),
                        admin_model.UserRestrictBanDetail.is_active == False,
                        admin_model.UserRestrictBanDetail.is_deleted == False,
                    )
                    .scalar()
                )

                # print(subq_min_enforce_action_at)
                consecutive_violation_query = db.query(
                    admin_model.UserRestrictBanDetail
                ).filter(
                    admin_model.UserRestrictBanDetail.user_id == restrict_user_id,
                    admin_model.UserRestrictBanDetail.enforce_action_at
                    == subq_min_enforce_action_at,
                )

                consecutive_violation = consecutive_violation_query.first()
                if consecutive_violation:
                    # enforce next violation
                    consecutive_violation_query.update(
                        {"is_active": True}, synchronize_session=False
                    )

                    # get user
                    user = user_service.get_user_by_id(
                        consecutive_violation.user_id, ["ACT", "PBN", "DEL"], db
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK", "INA"]:
                        user.status = consecutive_violation.status  # status update
                else:
                    user = user_service.get_user_by_id(
                        restrict_user_id, ["ACT", "TBN", "PBN", "DEL"], db
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK", "INA"]:
                        user.status = "ACT"

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error: ", exc)

    print("Restrict Users. Job Done")


def remove_ban_on_user_after_duration_expiration(db: Session = next(get_db())):
    remove_banned_users_query = (
        admin_service.get_temp_banned_users_duration_expired_query(db_session=db)
    )

    remove_banned_users = remove_banned_users_query.all()

    if remove_banned_users:
        try:
            # update is_active to False to all expired temp bans
            remove_banned_users_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            # get user ids
            remove_banned_user_ids_report_ids = [
                (item.user_id, item.report_id) for item in remove_banned_users
            ]

            # for every user id, check if there is any consecutive violation.
            # Since we have already updated is_active to False of the current active restrict/ban, we need to exclude that entry while getting next violation, so we use report_id in filter
            # if there is any, then enforce that violation i.e. update is_active to True, also if user current status is DAH/DAK/PDH/PDK/INA then don't update status, else update
            # if there is no consecutive violation then check current user status, if it is DAH/DAK/PDH/PDK/INA then don't update status, else update
            # there can be no consecutive violation for status already PBN
            for banned_user_id, banned_report_id in remove_banned_user_ids_report_ids:
                # order_by is for get the rows in a specific order,it is read only, not for updating the rows
                # consecutive_violation_query = (
                #     db.query(admin_model.UserRestrictBanDetail)
                #     .filter(
                #         admin_model.UserRestrictBanDetail.user_id == banned_user_id,
                #         admin_model.UserRestrictBanDetail.enforce_action_at
                #         > func.now(),
                #         admin_model.UserRestrictBanDetail.is_active == False,
                #         admin_model.UserRestrictBanDetail.is_deleted == False,
                #     )
                #     .order_by(admin_model.UserRestrictBanDetail.enforce_action_at.asc())
                # )

                # subquery to get the next nearest enforce_action_at which is greater than now(), scalar is used to directly fetch the value of single column value from the query
                subq_min_enforce_action_at = (
                    db.query(
                        func.min(admin_model.UserRestrictBanDetail.enforce_action_at)
                    )
                    .filter(
                        admin_model.UserRestrictBanDetail.user_id == banned_user_id,
                        admin_model.UserRestrictBanDetail.report_id
                        != banned_report_id,  # exclude the current deactivated restrict/ban entry
                        admin_model.UserRestrictBanDetail.is_active == False,
                        admin_model.UserRestrictBanDetail.is_deleted == False,
                        admin_model.UserRestrictBanDetail.enforce_action_at
                        <= func.now(),
                    )
                    .scalar()
                )

                consecutive_violation_query = db.query(
                    admin_model.UserRestrictBanDetail
                ).filter(
                    admin_model.UserRestrictBanDetail.user_id == banned_user_id,
                    admin_model.UserRestrictBanDetail.enforce_action_at
                    == subq_min_enforce_action_at,
                )
                consecutive_violation = consecutive_violation_query.first()

                if consecutive_violation:
                    # enforce next violation
                    consecutive_violation_query.update(
                        {"is_active": True},
                        synchronize_session=False,
                    )

                    # get user
                    user = user_service.get_user_by_id(
                        user_id=consecutive_violation.user_id,
                        status_not_in_list=["ACT", "PBN", "DEL"],
                        db_session=db,
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK", "INA"]:
                        user.status = consecutive_violation.status  # status update
                else:
                    user = user_service.get_user_by_id(
                        user_id=banned_user_id,
                        status_not_in_list=["ACT", "RSP", "RSF", "PBN", "DEL"],
                        db_session=db,
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK", "INA"]:
                        user.status = "ACT"  # status update

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error: ", exc)

    print("Ban Users. Job Done")


def user_inactivity_delete(db: Session = next(get_db())):
    # get all user auth track entries whose last entry has passed 6 months, recent ones
    inactive_auth_entries = auth_service.user_auth_track_user_inactivity_delete(
        db_session=db
    )
    if inactive_auth_entries:
        try:
            for user in inactive_auth_entries:
                user.status = "PDH"

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

    print("Inactive Delete Users. Done")


def user_inactivity_inactive(db: Session = next(get_db())):
    # get all user auth track entries whose last entry has passed 3 months, recent ones
    inactive_auth_entries = auth_service.user_auth_track_user_inactivity_inactive(
        db_session=db
    )
    if inactive_auth_entries:
        # fetch user ids
        inactive_user_ids = [user.user_id for user in inactive_auth_entries]

        # get the users
        users_to_be_deleted = user_service.get_all_users_by_id(
            user_id_list=inactive_user_ids,
            status_in_list=["ACT", "RSP", "RSF", "TBN"],
            db_session=db,
        )
        if users_to_be_deleted:
            try:
                for user in users_to_be_deleted:
                    user.status = "INA"

                db.commit()
            except SQLAlchemyError as exc:
                db.rollback()
                print("SQL Error:", exc)

    print("Inactive Users. Done")


# def reduce_violation_score_quarterly(db_session = next(get_db())):
#     # get the user ids of latest reports which are resolved, appeals for reports if any are not accepted, and are older than 3 months
#     # meaning there should be no violation of user in last three months for score to reduce by 25%
