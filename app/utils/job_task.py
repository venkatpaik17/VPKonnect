from http.client import HTTPException

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import admin as admin_model
from app.services import admin as admin_service
from app.services import user as user_service


def delete_user_after_deactivation_period_expiration(db: Session = next(get_db())):
    delete_entries_query = user_service.check_deactivation_expiration_query(db)
    users_to_be_delete = delete_entries_query.all()
    if users_to_be_delete:
        try:
            delete_entries_query.update(
                {"status": "DEL", "is_deleted": True}, synchronize_session=False
            )
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error: ", exc)

    print("Delete Users. Job Done")


def remove_restriction_on_user_after_duration_expiration(db: Session = next(get_db())):
    remove_restrict_users_query = (
        admin_service.get_restricted_users_duration_expired_query(db)
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
            remove_restrict_user_ids = [item.user_id for item in remove_restrict_users]

            # for every user id, check if there is any consecutive violation.
            # if there is any, then enforce that violation i.e. update is_active to True, also if user current status is DAH/DAK/PDH/PDK then don't update status, else update
            # if there is no consecutive violation then check current user status, if it is DAH/DAK/PDH/PDK then don't update status, else update
            for restrict_user_id in remove_restrict_user_ids:
                consecutive_violation_query = (
                    db.query(admin_model.UserRestrictBanDetail)
                    .filter(
                        admin_model.UserRestrictBanDetail.user_id == restrict_user_id,
                        admin_model.UserRestrictBanDetail.enforce_action_at
                        > func.now(),
                        admin_model.UserRestrictBanDetail.is_active == False,
                        admin_model.UserRestrictBanDetail.is_deleted == False,
                    )
                    .order_by(admin_model.UserRestrictBanDetail.enforce_action_at.asc())
                )

                consecutive_violation = consecutive_violation_query.first()

                if consecutive_violation:
                    consecutive_violation_query.update(
                        {"is_active": True}, synchronize_session=False
                    )

                    user = user_service.get_user_by_id(
                        consecutive_violation.user_id, ["ACT", "DEL"], db
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK"]:
                        user.status = consecutive_violation.status
                else:
                    user = user_service.get_user_by_id(
                        restrict_user_id, ["ACT", "TBN", "PBN", "DEL"], db
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK"]:
                        user.status = "ACT"

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error: ", exc)

    print("Restrict Users. Job Done")
