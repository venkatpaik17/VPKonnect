from datetime import timedelta
from logging import Logger

import requests

# from pydantic import EmailStr
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.db_sqlalchemy import metadata
from app.db.session import get_db
from app.models import admin as admin_model
from app.models import comment as comment_model
from app.models import post as post_model
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import log as log_utils
from app.utils import operation as operation_utils

# reflect database schema into the MetaData object
metadata.reflect(views=True)


def delete_user_after_deactivation_period_expiration():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    # get all delete schedule duration expiry entries
    scheduled_delete_entries = (
        user_service.check_deactivation_expiration_for_scheduled_delete(db_session=db)
    )
    # print(scheduled_delete_entries[0].__dict__ if scheduled_delete_entries else None)
    try:
        if scheduled_delete_entries:
            # fetch user ids
            scheduled_delete_user_ids = [
                user.user_id for user in scheduled_delete_entries
            ]
            # print(scheduled_delete_user_ids)
            # get the users
            users_to_be_deleted = user_service.get_all_users_by_id(
                user_id_list=scheduled_delete_user_ids,
                status_in_list=["PDH", "PDB", "PDI"],
                db_session=db,
            )
            if users_to_be_deleted:
                # print(users_to_be_deleted[0].__dict__)
                for user in users_to_be_deleted:
                    user.status = "DEL"
                    user.is_deleted = True

                db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Delete Users. Job Done")
    print("Delete Users. Job Done")


def remove_restriction_on_user_after_duration_expiration():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    remove_restrict_users_query = (
        admin_service.get_restricted_users_duration_expired_query(db_session=db)
    )
    remove_restrict_users = remove_restrict_users_query.all()
    # print(remove_restrict_users)
    try:
        if remove_restrict_users:
            # update is_active to False to all expired restrictions
            remove_restrict_users_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            # get report ids
            remove_restrict_report_ids = [
                item.report_id for item in remove_restrict_users
            ]

            # close pending appeals of appeal type account
            restrict_users_pending_appeals = (
                admin_service.get_all_appeals_report_id_content_type_list(
                    report_id_list=remove_restrict_report_ids,
                    status_in_list=["OPN", "URV"],
                    content_type="account",
                    db_session=db,
                )
            )
            if restrict_users_pending_appeals:
                for appeal in restrict_users_pending_appeals:
                    appeal.status = "CSD"
                    appeal.moderator_note = "AE"  # appeal expired

            # get the user ids
            remove_restrict_user_ids = [item.user_id for item in remove_restrict_users]

            # get enforce_action_at
            remove_restrict_users_enforce_action_at = [
                item.enforce_action_at for item in remove_restrict_users
            ]

            remove_restrict_user_ids_report_ids_enforce_action_at = list(
                zip(
                    remove_restrict_user_ids,
                    remove_restrict_report_ids,
                    remove_restrict_users_enforce_action_at,
                )
            )

            send_mail = False
            consecutive_violation = None
            user = None
            # for every user id, check if there is any consecutive violation.
            # Since we have already updated is_active to False of the current active restrict/ban, we need to exclude that entry while getting next violation, so we use report_id in filter
            # if there is any, then enforce that violation i.e. update is_active to True, also if user current status is DAH/PDH/INA then don't update status, else update
            # if there is no consecutive violation then check current user status, if it is DAH/PDH/INA then don't update status, else update
            # there can be no consecutive violation for status already PBN
            for (
                restrict_user_id,
                restrict_report_id,
                restrict_enforce_action_at,
            ) in remove_restrict_user_ids_report_ids_enforce_action_at:
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

                # get user, its status should be RSP/RSF or DAH/INA/PDH
                user = user_service.get_user_by_id(
                    user_id=str(restrict_user_id),
                    status_not_in_list=["ACT", "TBN", "PBN", "PDB", "PDI", "DEL"],
                    db_session=db,
                )

                if user:
                    # To get the next nearest enforce_action_at which is greater than now(), scalar is used to directly fetch the value of single column value from the query
                    subq_min_enforce_action_at = (
                        db.query(
                            func.min(
                                admin_model.UserRestrictBanDetail.enforce_action_at
                            )
                        )
                        .filter(
                            admin_model.UserRestrictBanDetail.user_id
                            == restrict_user_id,
                            admin_model.UserRestrictBanDetail.report_id
                            != restrict_report_id,  # exclude the current deactivated restrict/ban entry
                            admin_model.UserRestrictBanDetail.enforce_action_at
                            <= func.now(),
                            admin_model.UserRestrictBanDetail.enforce_action_at
                            > restrict_enforce_action_at,
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
                        admin_model.UserRestrictBanDetail.is_deleted == False,
                    )

                    consecutive_violation = consecutive_violation_query.first()

                    user_inactive_deactivated = ["DAH", "PDH", "INA"]
                    if consecutive_violation:
                        # enforce next violation
                        consecutive_violation_query.update(
                            {"is_active": True}, synchronize_session=False
                        )

                        operation_utils.consecutive_violation_operations(
                            consecutive_violation=consecutive_violation, db=db
                        )

                        # update user status
                        if user.status not in user_inactive_deactivated or (
                            user.status in user_inactive_deactivated
                            and consecutive_violation.status == "PBN"
                            and user.status != "PDH"
                        ):
                            user.status = consecutive_violation.status

                        # send email if status is TBN/PBN
                        if consecutive_violation.status == "PBN" or (
                            consecutive_violation.status == "TBN"
                            and user.status not in user_inactive_deactivated
                        ):
                            send_mail = True

                    else:
                        if user.status not in user_inactive_deactivated:
                            user.status = "ACT"
                else:
                    raise Exception(
                        "Error. User associated with the restriction not found"
                    )

            db.commit()

            if user and consecutive_violation and send_mail:
                url = "http://127.0.0.1:8000/api/v0/users/send-ban-mail"
                json_data = {
                    "status": consecutive_violation.status,
                    "email": user.email,
                    "username": user.username,
                    "duration": consecutive_violation.duration,
                    "enforced_action_at": consecutive_violation.enforce_action_at.isoformat(),
                }

                response = None
                try:
                    # Make the POST request with JSON body parameters and a timeout
                    response = requests.post(url, json=json_data, timeout=3)
                    response.raise_for_status()
                    logger.info("Request sent to %s successfully", url)
                except requests.Timeout as e:
                    logger.error(e, exc_info=True)
                    raise e
                except requests.HTTPError as err:
                    logger.error(err, exc_info=True)
                    raise err
                except requests.RequestException as exc:
                    logger.error(exc, exc_info=True)
                    raise exc

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    except requests.RequestException as exc:
        db.rollback()
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Restrict Users. Job Done")
    print("Restrict Users. Job Done")


def remove_ban_on_user_after_duration_expiration():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()
    remove_banned_users_query = (
        admin_service.get_temp_banned_users_duration_expired_query(db_session=db)
    )

    remove_banned_users = remove_banned_users_query.all()
    try:
        if remove_banned_users:
            # update is_active to False to all expired temp bans
            remove_banned_users_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            # get report ids
            remove_banned_report_ids = [item.report_id for item in remove_banned_users]

            # close pending appeals of appeal type account
            banned_users_pending_appeals = (
                admin_service.get_all_appeals_report_id_content_type_list(
                    report_id_list=remove_banned_report_ids,
                    status_in_list=["OPN", "URV"],
                    content_type="account",
                    db_session=db,
                )
            )
            if banned_users_pending_appeals:
                for appeal in banned_users_pending_appeals:
                    appeal.status = "CSD"
                    appeal.moderator_note = "AE"  # appeal expired

            # get user ids
            remove_banned_user_ids = [item.user_id for item in remove_banned_users]

            # get enforce_action_at
            remove_banned_users_enforce_action_at = [
                item.enforce_action_at for item in remove_banned_users
            ]

            remove_banned_user_ids_report_ids_enforce_action_at = list(
                zip(
                    remove_banned_user_ids,
                    remove_banned_report_ids,
                    remove_banned_users_enforce_action_at,
                )
            )

            send_mail = False
            consecutive_violation = None
            user = None
            # for every user id, check if there is any consecutive violation.
            # Since we have already updated is_active to False of the current active restrict/ban, we need to exclude that entry while getting next violation, so we use report_id in filter
            # if there is any, then enforce that violation i.e. update is_active to True, also if user current status is DAH/PDH/INA then don't update status, else update
            # if there is no consecutive violation then check current user status, if it is DAH/PDH/INA then don't update status, else update
            # there can be no consecutive violation for status already PBN
            for (
                banned_user_id,
                banned_report_id,
                banned_user_enforce_action_at,
            ) in remove_banned_user_ids_report_ids_enforce_action_at:
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

                # get user
                user = user_service.get_user_by_id(
                    user_id=banned_user_id,
                    status_not_in_list=[
                        "ACT",
                        "RSP",
                        "RSF",
                        "PBN",
                        "PDB",
                        "PDI",
                        "DEL",
                    ],
                    db_session=db,
                )
                if user:
                    # To get the next nearest enforce_action_at which is greater than now(), scalar is used to directly fetch the value of single column value from the query
                    subq_min_enforce_action_at = (
                        db.query(
                            func.min(
                                admin_model.UserRestrictBanDetail.enforce_action_at
                            )
                        )
                        .filter(
                            admin_model.UserRestrictBanDetail.user_id == banned_user_id,
                            admin_model.UserRestrictBanDetail.report_id
                            != banned_report_id,  # exclude the current deactivated restrict/ban entry
                            admin_model.UserRestrictBanDetail.is_active == False,
                            admin_model.UserRestrictBanDetail.is_deleted == False,
                            admin_model.UserRestrictBanDetail.enforce_action_at
                            <= func.now(),
                            admin_model.UserRestrictBanDetail.enforce_action_at
                            > banned_user_enforce_action_at,
                        )
                        .scalar()
                    )

                    consecutive_violation_query = db.query(
                        admin_model.UserRestrictBanDetail
                    ).filter(
                        admin_model.UserRestrictBanDetail.user_id == banned_user_id,
                        admin_model.UserRestrictBanDetail.enforce_action_at
                        == subq_min_enforce_action_at,
                        admin_model.UserRestrictBanDetail.is_deleted == False,
                    )
                    consecutive_violation = consecutive_violation_query.first()

                    user_inactive_deactivated = ["DAH", "PDH", "INA"]
                    if consecutive_violation:
                        # enforce next violation
                        consecutive_violation_query.update(
                            {"is_active": True},
                            synchronize_session=False,
                        )

                        operation_utils.consecutive_violation_operations(
                            consecutive_violation=consecutive_violation, db=db
                        )

                        # update user status
                        if user.status not in user_inactive_deactivated or (
                            user.status in user_inactive_deactivated
                            and consecutive_violation.status == "PBN"
                            and user.status != "PDH"
                        ):
                            user.status = consecutive_violation.status

                        # send email if status is TBN/PBN
                        if consecutive_violation.status == "PBN" or (
                            consecutive_violation.status == "TBN"
                            and user.status not in user_inactive_deactivated
                        ):
                            send_mail = True
                    else:
                        if user.status not in user_inactive_deactivated:
                            user.status = "ACT"  # status update
                else:
                    raise Exception(
                        "Error. User associated with the restriction not found"
                    )

            db.commit()

            if user and consecutive_violation and send_mail:
                url = "http://127.0.0.1:8000/api/v0/users/send-ban-mail"
                json_data = {
                    "status": consecutive_violation.status,
                    "email": user.email,
                    "username": user.username,
                    "duration": consecutive_violation.duration,
                    "enforced_action_at": consecutive_violation.enforce_action_at.isoformat(),
                }

                response = None
                try:
                    # Make the POST request with JSON body parameters and a timeout
                    response = requests.post(url, json=json_data, timeout=3)
                    response.raise_for_status()
                    logger.info("Request sent to %s successfully", url)
                except requests.Timeout as e:
                    logger.error(e, exc_info=True)
                    raise e
                except requests.HTTPError as err:
                    logger.error(err, exc_info=True)
                    raise err
                except requests.RequestException as exc:
                    logger.error(exc, exc_info=True)
                    raise exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    except requests.RequestException as exc:
        db.rollback()
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Ban Users. Job Done")
    print("Ban Users. Job Done")


def user_inactivity_delete():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    send_mail = False
    inactive_user_emails = list()

    # get all users whose user auth track entries last entry has passed 6/12 months, recent ones
    inactive_auth_entries = auth_service.user_auth_track_user_inactivity_delete(
        db_session=db
    )

    # get user ids
    inactive_user_ids = [user.id for user in inactive_auth_entries]

    # check if the users have active restrict/ban, if yes then get the query
    users_active_restrict_ban_query = (
        admin_service.get_users_active_restrict_ban_entry_query(
            user_id_list=inactive_user_ids,
            status_in_list=["RSP", "RSF", "TBN"],
            db_session=db,
        )
    )

    try:
        if inactive_auth_entries:
            # revoke the restrict/ban if there's one, by changing is_active to False, since the user is to be deleted permanently, restrict/ban is meaningless after this
            users_active_restrict_ban_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            # get user emails
            inactive_user_emails = [user.email for user in inactive_auth_entries]

            # # generate request data link
            # request_data_link = "https://vpkonnect.in/accounts/data_request_form"
            # email_subject = "VPKonnect - Account Deletion Due to User Inactivity"
            # email_details = admin_schema.SendEmail(
            #     template="inactivity_delete_email.html",
            #     email=inactive_user_emails,
            #     body_info={
            #         "link": request_data_link,
            #     },
            # )
            # try:
            #     email_utils.send_email(email_subject, email_details, background_tasks)
            # except Exception as exc:
            #     print("Email error: ", exc)

            # get all open/under review reports and close them
            open_under_review_reports = (
                admin_service.get_all_reports_reporter_user_id_status(
                    reporter_user_id_list=inactive_user_ids,
                    status_in_list=["OPN", "URV"],
                    db_session=db,
                )
            )
            for report in open_under_review_reports:
                report.status = "CSD"
                report.moderator_note = "UDI"  # User deleted

            # change user status to PDI
            for user in inactive_auth_entries:
                user.status = "PDI"

            send_mail = True

        db.commit()

        if inactive_user_emails and send_mail:
            url = "http://127.0.0.1:8000/api/v0/users/send-delete-mail"
            json_data = {
                "email": inactive_user_emails,
                "subject": "VPKonnect - Account Deletion Due to User Inactivity",
                "template": "inactivity_delete_email.html",
            }

            response = None
            try:
                # Make the POST request with JSON body parameters and a timeout
                response = requests.post(url, json=json_data, timeout=3)
                response.raise_for_status()
                logger.info("Request sent to %s successfully", url)
            except requests.Timeout as e:
                logger.error(e, exc_info=True)
                raise e
            except requests.HTTPError as err:
                logger.error(err, exc_info=True)
                raise err
            except requests.RequestException as exc:
                logger.error(exc, exc_info=True)
                raise exc

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    except requests.RequestException as exc:
        db.rollback()
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Inactive Delete Users. Job Done")
    print("Inactive Delete Users. Job Done")


def user_inactivity_inactive():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    # get all user auth track entries whose last entry has passed 3 months, recent ones
    inactive_auth_entries = auth_service.user_auth_track_user_inactivity_inactive(
        db_session=db
    )
    try:
        if inactive_auth_entries:
            # fetch user ids
            inactive_user_ids = [user.user_id for user in inactive_auth_entries]

            # get the users
            users_to_be_inactivated = user_service.get_all_users_by_id(
                user_id_list=inactive_user_ids,
                status_in_list=["ACT", "RSP", "RSF", "TBN"],
                db_session=db,
            )
            if users_to_be_inactivated:
                for user in users_to_be_inactivated:
                    user.status = "INA"

                db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Inactive Users. Job Done")
    print("Inactive Users. Job Done")


# PBN 21 day appeal limit check
def delete_user_after_permanent_ban_appeal_limit_expiry():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    # join user_restrict_ban_detail and user_content_restrict_ban_appeal_detail tables
    # to get PBN users having no pending appeals expiring 21 day appeal limit
    pbn_users_with_no_pending_appeal = (
        db.query(admin_model.UserRestrictBanDetail)
        .join(
            admin_model.UserContentRestrictBanAppealDetail,
            admin_model.UserRestrictBanDetail.report_id
            == admin_model.UserContentRestrictBanAppealDetail.report_id,
            isouter=True,
        )
        .filter(
            admin_model.UserRestrictBanDetail.status == "PBN",
            admin_model.UserRestrictBanDetail.is_active == True,
            admin_model.UserRestrictBanDetail.is_deleted == False,
            (func.now() - timedelta(days=settings.pbn_appeal_submit_limit_days))
            >= admin_model.UserRestrictBanDetail.enforce_action_at,
            or_(
                admin_model.UserContentRestrictBanAppealDetail.id == None,
                and_(
                    admin_model.UserContentRestrictBanAppealDetail.status == "REJ",
                    admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
                ),
            ),
        )
        .all()
    )

    send_mail = False
    pbn_no_appeal_user_emails = list()
    try:
        if pbn_users_with_no_pending_appeal:
            # get user ids
            pbn_no_appeal_user_ids = [
                ban_entry.user_id for ban_entry in pbn_users_with_no_pending_appeal
            ]

            # get ban entry ids
            pbn_no_appeal_ban_entry_ids = [
                ban_entry.id for ban_entry in pbn_users_with_no_pending_appeal
            ]

            # get ban entries
            pbn_no_appeal_ban_entries = (
                admin_service.get_users_active_restrict_ban_entry_id(
                    restrict_ban_id_list=pbn_no_appeal_ban_entry_ids, db_session=db
                )
            )

            # get users
            pbn_no_appeal_users = user_service.get_all_users_by_id(
                user_id_list=pbn_no_appeal_user_ids,
                status_in_list=["PBN"],
                db_session=db,
            )

            # update is_active to False
            for ban_entry in pbn_no_appeal_ban_entries:
                ban_entry.is_active = False

            # get user emails
            pbn_no_appeal_user_emails = [user.email for user in pbn_no_appeal_users]

            # # generate request data link
            # request_data_link = "https://vpkonnect.in/accounts/data_request_form"
            # email_subject = "VPKonnect - Account Deletion Due to Appeal Limit Expiration"
            # email_details = admin_schema.SendEmail(
            #     template="appeal_limit_account_delete.html",
            #     email=pbn_no_appeal_user_emails,
            #     body_info={
            #         "link": request_data_link,
            #     },
            # )
            # try:
            #     email_utils.send_email(email_subject, email_details, background_tasks)
            # except Exception as exc:
            #     print("Email error: ", exc)

            # update user status to PDB
            for user in pbn_no_appeal_users:
                user.status = "PDB"

            send_mail = True

        db.commit()

        if pbn_no_appeal_user_emails and send_mail:
            url = "http://127.0.0.1:8000/api/v0/users/send-delete-mail"
            json_data = {
                "email": pbn_no_appeal_user_emails,
                "subject": "VPKonnect - Account Deletion Due to Appeal Limit Expiration",
                "template": "appeal_limit_account_delete.html",
            }

            response = None
            try:
                # Make the POST request with JSON body parameters and a timeout
                response = requests.post(url, json=json_data, timeout=3)
                response.raise_for_status()
                logger.info("Request sent to %s successfully", url)
            except requests.Timeout as e:
                logger.error(e, exc_info=True)
                raise e
            except requests.HTTPError as err:
                logger.error(err, exc_info=True)
                raise err
            except requests.RequestException as exc:
                logger.error(exc, exc_info=True)
                raise exc

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    except requests.RequestException as exc:
        db.rollback()
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info(
        "PBN %s days Appeal Limit. Job Done", settings.pbn_appeal_submit_limit_days
    )
    print(f"PBN {settings.pbn_appeal_submit_limit_days} days Appeal Limit. Job Done")


# post/comment 28 day appeal limit check
def delete_content_after_ban_appeal_limit_expiry():
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    # join post and appeal table to get the posts to be deleted
    posts_with_no_pending_appeal = (
        db.query(post_model.Post)
        .join(
            admin_model.UserContentRestrictBanAppealDetail,
            post_model.Post.id
            == admin_model.UserContentRestrictBanAppealDetail.content_id,
            isouter=True,
        )
        .filter(
            post_model.Post.status == "BAN",
            post_model.Post.is_deleted == False,
            func.now()
            >= (
                post_model.Post.updated_at
                + timedelta(days=settings.content_appeal_submit_limit_days)
            ),
            or_(
                admin_model.UserContentRestrictBanAppealDetail.id == None,
                and_(
                    admin_model.UserContentRestrictBanAppealDetail.status == "REJ",
                    admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
                ),
            ),
        )
        .all()
    )

    # join comment and appeal table to get the comments to be deleted
    comments_with_no_pending_appeal = (
        db.query(comment_model.Comment)
        .join(
            admin_model.UserContentRestrictBanAppealDetail,
            comment_model.Comment.id
            == admin_model.UserContentRestrictBanAppealDetail.content_id,
            isouter=True,
        )
        .filter(
            comment_model.Comment.status == "BAN",
            comment_model.Comment.is_deleted == False,
            func.now()
            >= (
                comment_model.Comment.updated_at
                + timedelta(days=settings.content_appeal_submit_limit_days)
            ),
            or_(
                admin_model.UserContentRestrictBanAppealDetail.id == None,
                and_(
                    admin_model.UserContentRestrictBanAppealDetail.status == "REJ",
                    admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
                ),
            ),
        )
        .all()
    )

    try:
        if posts_with_no_pending_appeal:
            # get all post ids of the posts to be deleted
            post_ids = [post_entry.id for post_entry in posts_with_no_pending_appeal]

            # get posts query
            posts_to_be_deleted_query = post_service.get_all_posts_by_id_query(
                post_id_list=post_ids, status_in_list=["BAN"], db_session=db
            )

            # update the is_ban_final to True
            posts_to_be_deleted_query.update(
                {"is_ban_final": True},
                synchronize_session=False,
            )

        if comments_with_no_pending_appeal:
            # get all comment ids of the posts to be deleted
            comment_ids = [
                comment_entry.id for comment_entry in comments_with_no_pending_appeal
            ]

            # get comments query
            comments_to_be_deleted_query = comment_service.get_all_comments_by_id_query(
                comment_id_list=comment_ids, status_in_list=["BAN"], db_session=db
            )

            # update the is_ban_final to True
            comments_to_be_deleted_query.update(
                {"is_ban_final": True},
                synchronize_session=False,
            )

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info(
        "Post/Comment %s days Appeal Limit. Job Done",
        settings.content_appeal_submit_limit_days,
    )
    print(
        f"Post/Comment {settings.content_appeal_submit_limit_days} days Appeal Limit. Job Done",
    )


def close_appeal_after_duration_limit_expiration():
    # this is for PBN and post/comment ban appeals only
    # for RSP, RSF and TBN it is handled during removing restrict/ban job
    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    try:
        # PBN
        # join user_restrict_ban_detail with user_content_restrict_ban_appeal_detail
        # to get PBN user pending appeals which have crossed 30 day limit
        pbn_users_pending_appeal_expired_limit = (
            db.query(
                admin_model.UserRestrictBanDetail.id.label("ban_id"),
                admin_model.UserRestrictBanDetail.user_id.label("user_id"),
                admin_model.UserContentRestrictBanAppealDetail.id.label("appeal_id"),
            )
            .join(
                admin_model.UserContentRestrictBanAppealDetail,
                admin_model.UserRestrictBanDetail.report_id
                == admin_model.UserContentRestrictBanAppealDetail.report_id,
            )
            .filter(
                admin_model.UserRestrictBanDetail.status == "PBN",
                admin_model.UserRestrictBanDetail.is_active == True,
                admin_model.UserRestrictBanDetail.is_deleted == False,
                admin_model.UserContentRestrictBanAppealDetail.status.in_(
                    ["OPN", "URV"]
                ),
                func.now()
                >= (
                    admin_model.UserContentRestrictBanAppealDetail.created_at
                    + timedelta(days=settings.appeal_process_duration_limit_days)
                ),
                admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
            )
            .all()
        )
        if pbn_users_pending_appeal_expired_limit:
            # get ban ids
            pbn_expired_pending_appeal_ban_entry_ids = [
                getattr(join_entry, "ban_id")
                for join_entry in pbn_users_pending_appeal_expired_limit
            ]

            # get user ids
            pbn_expired_pending_appeal_user_ids = [
                getattr(join_entry, "user_id")
                for join_entry in pbn_users_pending_appeal_expired_limit
            ]

            # get appeal ids
            pbn_expired_pending_appeal_ids = [
                getattr(join_entry, "appeal_id")
                for join_entry in pbn_users_pending_appeal_expired_limit
            ]

            # get ban entries
            pbn_expired_pending_appeal_ban_entries = (
                admin_service.get_users_active_restrict_ban_entry_id(
                    restrict_ban_id_list=pbn_expired_pending_appeal_ban_entry_ids,
                    db_session=db,
                )
            )

            # get users
            pbn_expired_pending_appeal_users = user_service.get_all_users_by_id(
                user_id_list=pbn_expired_pending_appeal_user_ids,
                status_in_list=["PBN"],
                db_session=db,
            )

            # get appeals
            pbn_expired_pending_appeals = admin_service.get_appeals_by_id(
                appeal_id_list=pbn_expired_pending_appeal_ids, db_session=db
            )

            # update appeal status and moderator_note
            for appeal in pbn_expired_pending_appeals:
                appeal.status = "CSD"
                appeal.moderator_note = "AE"  # appeal expired

            for ban_entry in pbn_expired_pending_appeal_ban_entries:
                ban_entry.is_active = False

            for user in pbn_expired_pending_appeal_users:
                user.status = "PDB"

        # post/comment
        # query the user_content_restrict_ban_appeal_detail for OPN/URV using content_type as post or comment
        # filter for 30 day process limit
        # change the appeal status to CSD
        # change is_ban_final to True for post/comment
        pending_appeals_process_limit_expiry = (
            db.query(admin_model.UserContentRestrictBanAppealDetail)
            .filter(
                admin_model.UserContentRestrictBanAppealDetail.content_type.in_(
                    ["post", "comment"]
                ),
                admin_model.UserContentRestrictBanAppealDetail.status.in_(
                    ["OPN", "URV"]
                ),
                func.now()
                >= (
                    admin_model.UserContentRestrictBanAppealDetail.created_at
                    + timedelta(days=settings.appeal_process_duration_limit_days)
                ),
                admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
            )
            .all()
        )

        if pending_appeals_process_limit_expiry:
            for appeal in pending_appeals_process_limit_expiry:
                appeal.status = "CSD"
                appeal.moderator_note = "AE"  # appeal expired

            # get the content ids
            appealed_post_ids = {
                appeal_entry.content_id
                for appeal_entry in pending_appeals_process_limit_expiry
                if appeal_entry.content_type == "post"
            }
            appealed_comment_ids = {
                appeal_entry.content_id
                for appeal_entry in pending_appeals_process_limit_expiry
                if appeal_entry.content_type == "comment"
            }

            # get the posts
            appealed_posts_query = post_service.get_all_posts_by_id_query(
                post_id_list=list(appealed_post_ids),
                status_in_list=["BAN"],
                db_session=db,
            )

            # get the comments
            appealed_comments_query = comment_service.get_all_comments_by_id_query(
                comment_id_list=list(appealed_comment_ids),
                status_in_list=["BAN"],
                db_session=db,
            )

            # update is_ban_final to True
            appealed_posts_query.update(
                {"is_ban_final": True},
                synchronize_session=False,
            )
            appealed_comments_query.update(
                {"is_ban_final": True},
                synchronize_session=False,
            )

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Close Appeal. Job Done")
    print("Close Appeal. Job Done")


def reduce_violation_score_quarterly():
    # get the user ids of latest reports which are resolved, appeals for reports if any are not accepted, and are older than 3 months
    # meaning there should be no violation of user in last three months for score to reduce by 50%

    db: Session = next(get_db())
    logger: Logger = log_utils.get_logger()

    # join user_content_report_detail and user_content_restrict_ban_appeal_detail
    report_appeal_join = (
        db.query(admin_model.UserContentReportDetail.reported_user_id)
        .join(
            admin_model.UserContentRestrictBanAppealDetail,
            admin_model.UserContentReportDetail.id
            == admin_model.UserContentRestrictBanAppealDetail.report_id,
            isouter=True,
        )
        .filter(
            admin_model.UserContentReportDetail.status == "RSD",
            or_(
                admin_model.UserContentRestrictBanAppealDetail.status.is_(None),
                admin_model.UserContentRestrictBanAppealDetail.status.notin_(
                    ["ACP", "ACR"]
                ),
            ),
            func.now()
            > (
                admin_model.UserContentReportDetail.updated_at
                + timedelta(days=settings.violation_score_reduction_days)
            ),
            admin_model.UserContentReportDetail.is_deleted == False,
            or_(
                admin_model.UserContentRestrictBanAppealDetail.is_deleted.is_(None),
                admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
            ),
        )
        .all()
    )

    # get the user ids
    no_violation_three_months_user_ids = [item[0] for item in report_appeal_join]

    # fetch guideline_violation_score entry and reduce the scores by 50% in all
    guideline_violation_score_entries_query = (
        admin_service.get_users_guideline_violation_score_query(
            user_id_list=no_violation_three_months_user_ids, db_session=db
        )
    )
    guideline_violation_score_entries = guideline_violation_score_entries_query.filter(
        func.now()
        > admin_model.GuidelineViolationScore.updated_at
        + timedelta(days=settings.violation_score_reduction_days)
    ).all()
    try:
        if guideline_violation_score_entries:
            reduce_rate = 0.50
            for entry in guideline_violation_score_entries:
                entry.post_score = round(entry.post_score * reduce_rate)
                entry.comment_score = round(entry.comment_score * reduce_rate)
                entry.message_score = round(entry.message_score * reduce_rate)
                entry.final_violation_score = round(
                    entry.final_violation_score * reduce_rate
                )

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
    finally:
        db.close()

    logger.info("Score Reduction. Job Done")
    print("Score Reduction. Job Done")


# def operations_after_appeal_accept():
#     # Access the reflected view
#     join_view = metadata.tables["appeal_restrict_join_view"]
#     db = next(get_db())

#     try:
#         # query the view
#         appeal_restrict_join_entries = db.query(join_view).all()
#         print(len(appeal_restrict_join_entries))
#         print("Hello1")
#         error_appeal_ids = []
#         for restrict_ban_appeal_entry in appeal_restrict_join_entries:
#             try:
#                 query_user_id = restrict_ban_appeal_entry.user_id
#                 query_report_id = restrict_ban_appeal_entry.report_id
#                 query_content_id = None
#                 query_content_type = None
#                 query_status = None

#                 if restrict_ban_appeal_entry.appeal_content_type == "account":
#                     print("Account")
#                     # Appeal type: account, Report type: account
#                     if (
#                         restrict_ban_appeal_entry.user_restrict_ban_content_type
#                         == "account"
#                     ):
#                         print("Account-Account")
#                         # fetch the flagged posts from account_report_flagged_content, get all or partial no of posts which are banned, change the status from BAN to PUB
#                         # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
#                         # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
#                         account_report_valid_flagged_content = admin_service.get_all_valid_flagged_content_account_report_id(
#                             report_id=query_report_id, db_session=db
#                         )
#                         account_report_flagged_content_ids = [
#                             content[0]
#                             for content in account_report_valid_flagged_content
#                         ]
#                         no_of_flagged_posts = len(account_report_flagged_content_ids)

#                         account_report_flagged_posts = (
#                             post_service.get_all_posts_by_id_query(
#                                 post_id_list=account_report_flagged_content_ids,
#                                 status_in_list=["BAN"],
#                                 db_session=db,
#                             ).all()
#                         )
#                         no_of_banned_posts = len(account_report_flagged_posts)

#                         for post in account_report_flagged_posts:
#                             post.status = "PUB"

#                         query_content_type = (
#                             restrict_ban_appeal_entry.user_restrict_ban_content_type
#                         )
#                         operation_utils.guideline_violation_score_last_added_score_operation(
#                             user_id=query_user_id,
#                             report_id=query_report_id,
#                             ban_content_type=query_content_type,
#                             db=db,
#                             account_report_flagged_content=no_of_flagged_posts,
#                             content_to_be_unbanned=no_of_banned_posts,
#                             content_already_unbanned=(
#                                 no_of_flagged_posts - no_of_banned_posts
#                             ),
#                         )

#                         query_status = (
#                             restrict_ban_appeal_entry.user_restrict_ban_status
#                         )
#                         operation_utils.user_restrict_ban_detail_user_operation(
#                             user_id=query_user_id,
#                             report_id=query_report_id,
#                             status=query_status,
#                             db=db,
#                         )

#                     # Appeal type: account, Report type: post/comment
#                     elif restrict_ban_appeal_entry.user_restrict_ban_content_type in (
#                         "post",
#                         "comment",
#                     ):
#                         # fetch the banned post/comment and change the status to PUB
#                         # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
#                         # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
#                         query_content_id = (
#                             restrict_ban_appeal_entry.user_restrict_ban_content_id
#                         )
#                         query_content_type = (
#                             restrict_ban_appeal_entry.user_restrict_ban_content_type
#                         )
#                         operation_utils.post_comment_operation(
#                             ban_content_id=query_content_id,
#                             ban_content_type=query_content_type,
#                             db=db,
#                         )

#                         operation_utils.guideline_violation_score_last_added_score_operation(
#                             user_id=query_user_id,
#                             report_id=query_report_id,
#                             ban_content_type=query_content_type,
#                             db=db,
#                             content_to_be_unbanned=1,
#                             content_already_unbanned=0,
#                         )

#                         query_status = (
#                             restrict_ban_appeal_entry.user_restrict_ban_status
#                         )
#                         operation_utils.user_restrict_ban_detail_user_operation(
#                             user_id=query_user_id,
#                             report_id=query_report_id,
#                             status=query_status,
#                             db=db,
#                         )

#                 elif restrict_ban_appeal_entry.appeal_content_type in (
#                     "post",
#                     "comment",
#                 ):
#                     if (
#                         restrict_ban_appeal_entry.appeal_content_type == "post"
#                         and restrict_ban_appeal_entry.user_restrict_ban_content_type
#                         == "account"
#                         and restrict_ban_appeal_entry.user_restrict_ban_status
#                         in ("RSP", "RSF")
#                     ):
#                         # fetch the flagged posts from account_report_flagged_content
#                         # fetch the appealed post, change the status to PUB
#                         # If all posts have their bans revoked then consider last added score and manage it, update is_removed to True
#                         #     Else consider only fraction of last added score
#                         # update guideline violation score table

#                         account_report_valid_flagged_content = admin_service.get_all_valid_flagged_content_account_report_id(
#                             report_id=query_report_id, db_session=db
#                         )
#                         account_report_flagged_content_ids = [
#                             content[0]
#                             for content in account_report_valid_flagged_content
#                         ]
#                         no_of_flagged_posts = len(account_report_flagged_content_ids)

#                         account_report_flagged_posts = (
#                             post_service.get_all_posts_by_id_query(
#                                 post_id_list=account_report_flagged_content_ids,
#                                 status_in_list=["PUB"],
#                                 db_session=db,
#                             ).all()
#                         )
#                         no_of_posts_already_unbanned = len(account_report_flagged_posts)

#                         query_content_id = restrict_ban_appeal_entry.appeal_content_id
#                         operation_utils.post_comment_operation(
#                             ban_content_id=query_content_id,
#                             ban_content_type=restrict_ban_appeal_entry.appeal_content_type,
#                             db=db,
#                         )

#                         query_content_type = (
#                             restrict_ban_appeal_entry.user_restrict_ban_content_type
#                         )
#                         operation_utils.guideline_violation_score_last_added_score_operation(
#                             user_id=query_user_id,
#                             report_id=query_report_id,
#                             ban_content_type=query_content_type,
#                             db=db,
#                             content_to_be_unbanned=1,
#                             content_already_unbanned=no_of_posts_already_unbanned,
#                             account_report_flagged_content=no_of_flagged_posts,
#                         )

#                         # Appeal type: post, Report type: account, (RSP/RSF, active restrict)
#                         if (
#                             restrict_ban_appeal_entry.user_restrict_ban_is_active
#                             == "True"
#                         ):
#                             # check if all the flagged posts have PUB status, if yes then revoke the restrict, else don't
#                             # if restrict is revoked, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
#                             if (
#                                 no_of_posts_already_unbanned + 1
#                             ) == no_of_flagged_posts:
#                                 query_status = (
#                                     restrict_ban_appeal_entry.user_restrict_ban_status
#                                 )
#                                 operation_utils.user_restrict_ban_detail_user_operation(
#                                     user_id=query_user_id,
#                                     report_id=query_report_id,
#                                     status=query_status,
#                                     db=db,
#                                 )

#                         # Appeal type: post, Report type: account (RSP/RSF, no active restrict)
#                         else:
#                             # all required operations are done before
#                             pass

#                     elif restrict_ban_appeal_entry.user_restrict_ban_content_type in (
#                         "post",
#                         "comment",
#                     ):
#                         # fetch the banned post/comment, update status to PUB
#                         query_content_id = (
#                             restrict_ban_appeal_entry.user_restrict_ban_content_id
#                         )
#                         query_content_type = (
#                             restrict_ban_appeal_entry.user_restrict_ban_content_type
#                         )
#                         operation_utils.post_comment_operation(
#                             ban_content_id=query_content_id,
#                             ban_content_type=query_content_type,
#                             db=db,
#                         )

#                         # Appeal type: post/comment, Report type: post/comment (active restrict/ban)
#                         if (
#                             restrict_ban_appeal_entry.user_restrict_ban_is_active
#                             == "True"
#                         ):
#                             # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
#                             # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status

#                             operation_utils.guideline_violation_score_last_added_score_operation(
#                                 user_id=query_user_id,
#                                 report_id=query_report_id,
#                                 ban_content_type=query_content_type,
#                                 db=db,
#                                 content_to_be_unbanned=1,
#                                 content_already_unbanned=0,
#                             )

#                             query_status = (
#                                 restrict_ban_appeal_entry.user_restrict_ban_status
#                             )
#                             operation_utils.user_restrict_ban_detail_user_operation(
#                                 user_id=query_user_id,
#                                 report_id=query_report_id,
#                                 status=query_status,
#                                 db=db,
#                             )

#                         # Appeal type: post/comment, Report type: post/comment (active restrict/ban concluded)
#                         elif (
#                             restrict_ban_appeal_entry.user_restrict_ban_is_active
#                             == "False"
#                         ):
#                             # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
#                             operation_utils.guideline_violation_score_last_added_score_operation(
#                                 user_id=query_user_id,
#                                 report_id=query_report_id,
#                                 ban_content_type=query_content_type,
#                                 db=db,
#                                 content_to_be_unbanned=1,
#                                 content_already_unbanned=0,
#                             )

#                         # Appeal type: post/comment, Report type: post/comment (no restrict/ban entry)
#                         elif (
#                             restrict_ban_appeal_entry.user_restrict_ban_is_active
#                             is None
#                         ):
#                             # required operation(s) are done before
#                             pass

#                 db.commit()
#             except SQLAlchemyError as exc:
#                 print("SQL Error:", exc)
#                 db.rollback()
#             except Exception as exc:
#                 print("Error", exc)
#                 db.rollback()

#             #
#     except Exception as exc:
#         print("Error", exc)
#         db.rollback()
#     finally:
#         db.close()

#     print("Appeal accept operations. Job Done.")
