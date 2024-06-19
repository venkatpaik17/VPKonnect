from datetime import timedelta

import requests
from fastapi import BackgroundTasks
from pydantic import EmailStr
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import admin as admin_model
from app.models import comment as comment_model
from app.models import post as post_model
from app.schemas import admin as admin_schema
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import email as email_utils


def delete_user_after_deactivation_period_expiration():
    db: Session = next(get_db())
    # get all delete schedule duration expiry entries
    scheduled_delete_entries = (
        user_service.check_deactivation_expiration_for_scheduled_delete(db_session=db)
    )
    # print(scheduled_delete_entries[0].__dict__ if scheduled_delete_entries else None)
    if scheduled_delete_entries:
        # fetch user ids
        scheduled_delete_user_ids = [user.user_id for user in scheduled_delete_entries]
        # print(scheduled_delete_user_ids)
        # get the users
        users_to_be_deleted = user_service.get_all_users_by_id(
            user_id_list=scheduled_delete_user_ids,
            status_in_list=["PDK", "PDH"],
            db_session=db,
        )
        if users_to_be_deleted:
            # print(users_to_be_deleted[0].__dict__)
            try:
                for user in users_to_be_deleted:
                    user.status = "DEL"
                    user.is_deleted = True
                    # print("HI2")

                db.commit()
            except SQLAlchemyError as exc:
                db.rollback()
                print("SQL Error: ", exc)

    print("Delete Users. Job Done")


def consecutive_violation_operations(
    consecutive_violation: admin_model.UserRestrictBanDetail, db: Session
):
    consecutive_violation_report_query = admin_service.get_a_report_by_report_id_query(
        report_id=str(consecutive_violation.report_id),
        status="FRS",
        db_session=db,
    )
    consecutive_violation_report = consecutive_violation_report_query.first()

    if not consecutive_violation_report:
        print("Report concerning the consecutive violation not found")
        raise Exception("Error. Report concerning the consecutive violation not found")

    consecutive_violation_report_query.update(
        {"status": "RSD"}, synchronize_session=False
    )

    related_reports_query = admin_service.get_related_reports_for_specific_report_query(
        case_number=consecutive_violation_report.case_number,
        reported_user_id=str(consecutive_violation_report.reported_user_id),
        reported_item_id=str(consecutive_violation_report.reported_item_id),
        reported_item_type=consecutive_violation_report.reported_item_type,
        status="FRR",
        moderator_id=consecutive_violation_report.moderator_id,
        db_session=db,
    ).filter(
        admin_model.UserContentReportDetail.report_reason
        == consecutive_violation_report.report_reason
    )
    related_reports = related_reports_query.all()

    if related_reports:
        for related_report in related_reports:
            related_report.status = "RSR"

    # get the guideline violation score entry using user_id got from reported_user_id
    # get last added score entry using score_id and report_id
    # update content score and final violation score based on report content type
    # update is_added to True in last added score entry
    violation_score_query = admin_service.get_user_guideline_violation_score_query(
        user_id=str(consecutive_violation_report.reported_user_id),
        db_session=db,
    )
    violation_score_entry = violation_score_query.first()
    if not violation_score_entry:
        print("Guideline Violation Score for user not found")
        raise Exception("Error. Guideline Violation Score for user not found")

    last_added_score_entry = admin_service.get_last_added_score(
        score_id=str(violation_score_entry.id),
        report_id=str(consecutive_violation_report.id),
        db_session=db,
        is_added=False,
    )
    if not last_added_score_entry:
        print("Last added score concerning the report and user not found")
        raise Exception(
            "Error. Last added score concerning the report and user not found"
        )

    # get the score type and curr score of that score type
    if consecutive_violation_report.reported_item_type == "post":
        score_type = "post_score"
        curr_score = violation_score_entry.post_score
    elif consecutive_violation_report.reported_item_type == "comment":
        score_type = "comment_score"
        curr_score = violation_score_entry.comment_score
    elif consecutive_violation_report.reported_item_type == "message":
        score_type = "message_score"
        curr_score = violation_score_entry.message_score
    # if reported item type is account, then use post_score, as posts reflect most of the account
    else:
        score_type = "post_score"
        curr_score = violation_score_entry.post_score

    new_content_score = curr_score + last_added_score_entry.last_added_score

    new_final_violation_score = (
        violation_score_entry.final_violation_score
        + last_added_score_entry.last_added_score
    )

    violation_score_query.update(
        {
            score_type: new_content_score,
            "final_violation_score": new_final_violation_score,
        },
        synchronize_session=False,
    )

    last_added_score_entry.is_added = True

    # if report content type is post/comment/message, then fetch the content using its id
    # change the status from FLB to BAN, if the status of the content is FLD then dont change the status, let it be
    # if report content type is account, then fetch the valid_flagged_content list from account_report_flagged_content table
    # iterate through the list and change the status from FLB to BAN, if the status of the content is FLD then dont change the status, let it be
    if consecutive_violation_report.reported_item_type == "account":
        valid_flagged_content = (
            admin_service.get_all_valid_flagged_content_account_report_id(
                report_id=consecutive_violation_report.id, db_session=db
            )
        )
        if not valid_flagged_content:
            raise Exception(
                "Error. Valid Flagged Content(s) associated with consecutive violation report not found"
            )

        valid_flagged_content_ids = [content[0] for content in valid_flagged_content]
        # we flag only posts for report type account, so content is basically post, valid_flagged_content_ids is a list of post ids
        for content_id in valid_flagged_content_ids:
            print(content_id)
            post = post_service.get_a_post(
                post_id=str(content_id),
                status_not_in_list=["PUB", "DRF", "HID", "DEL"],
                db_session=db,
            )
            if not post:
                raise Exception(
                    "Error. Valid Flagged Post associated with consecutive violation account report not found"
                )
            if post.status == "BAN":
                raise Exception(
                    "Error. Valid Flagged Post associated with consecutive violation account report already banned"
                )

            if post.status == "FLD":
                print("Valid Flagged Post already deleted. Status not changed to BAN")
            elif post.status == "FLB":
                post.status = "BAN"
    else:
        if consecutive_violation_report.reported_item_type == "post":
            post = post_service.get_a_post(
                post_id=str(consecutive_violation_report.reported_item_id),
                status_not_in_list=["PUB", "DRF", "HID", "DEL"],
                db_session=db,
            )
            if not post:
                raise Exception(
                    "Error. Post associated with consecutive violation report not found"
                )
            if post.status == "BAN":
                raise Exception(
                    "Error. Post associated with consecutive violation report already banned"
                )

            if post.status == "FLD":
                print("Flagged Post already deleted. Status not changed to BAN")
            elif post.status == "FLB":
                post.status = "BAN"

        elif consecutive_violation_report.reported_item_type == "comment":
            comment = comment_service.get_a_comment(
                comment_id=str(consecutive_violation_report.reported_item_id),
                status_not_in_list=["PUB", "HID", "DEL"],
                db_session=db,
            )
            if not comment:
                raise Exception(
                    "Error. Comment associated with consecutive violation report not found"
                )
            if comment.status == "BAN":
                raise Exception(
                    "Error. Comment associated with consecutive violation report already banned"
                )

            if comment.status == "FLD":
                print("Flagged Comment already deleted. Status not changed to BAN")
            elif comment.status == "FLB":
                comment.status = "BAN"


def remove_restriction_on_user_after_duration_expiration(
    background_tasks: BackgroundTasks,
):
    db: Session = next(get_db())
    remove_restrict_users_query = (
        admin_service.get_restricted_users_duration_expired_query(db_session=db)
    )
    remove_restrict_users = remove_restrict_users_query.all()
    # print(remove_restrict_users)
    if remove_restrict_users:
        try:
            # update is_active to False to all expired restrictions
            remove_restrict_users_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            # get report ids
            remove_restrict_report_ids = [
                item.report_id for item in remove_restrict_users
            ]

            # close pending appeals
            restrict_users_pending_appeals = (
                admin_service.get_all_appeals_report_id_list(
                    report_id_list=remove_restrict_report_ids,
                    status_in_list=["OPN", "URV"],
                    db_session=db,
                )
            )
            if restrict_users_pending_appeals:
                for appeal in restrict_users_pending_appeals:
                    appeal.status = "CSD"
                    appeal.moderator_note = "AE"  # appeal expired

            # get the user ids
            remove_restrict_user_ids = [item.user_id for item in remove_restrict_users]

            remove_restrict_user_ids_report_ids = list(
                zip(remove_restrict_user_ids, remove_restrict_report_ids)
            )

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

                user_inactive_deactivated = ["DAH", "DAK", "PDH", "PDK", "INA"]
                if consecutive_violation:
                    # enforce next violation
                    consecutive_violation_query.update(
                        {"is_active": True}, synchronize_session=False
                    )

                    # get user
                    user = user_service.get_user_by_id(
                        str(consecutive_violation.user_id),
                        ["ACT", "TBN", "PBN", "DEL"],
                        db,
                    )
                    if user:
                        consecutive_violation_operations(
                            consecutive_violation=consecutive_violation, db=db
                        )

                        # send email if status is TBN/PBN
                        if consecutive_violation.status == "PBN" or (
                            consecutive_violation.status == "TBN"
                            and user.status not in user_inactive_deactivated
                        ):
                            # generate appeal link
                            appeal_link = (
                                "https://vpkonnect.in/accounts/appeals/form_ban"
                            )

                            email_subject = "VPKonnect - Account Ban"
                            email_details = admin_schema.SendEmail(
                                template=(
                                    "permanent_ban_email.html"
                                    if consecutive_violation.status == "PBN"
                                    else "temporary_ban_email.html"
                                ),
                                email=[EmailStr(user.email)],
                                body_info={
                                    "username": user.username,
                                    "link": appeal_link,
                                    "days": consecutive_violation.duration // 24,
                                    "ban_enforced_datetime": consecutive_violation.enforce_action_at.strftime(
                                        "%b %d, %Y %H:%M %Z"
                                    ),
                                },
                            )

                            email_utils.send_email(
                                email_subject, email_details, background_tasks
                            )

                        # update user status
                        if user.status not in user_inactive_deactivated or (
                            user.status in user_inactive_deactivated
                            and consecutive_violation.status == "PBN"
                        ):
                            user.status = consecutive_violation.status
                else:
                    user = user_service.get_user_by_id(
                        restrict_user_id, ["ACT", "TBN", "PBN", "DEL"], db
                    )
                    if user and user.status not in user_inactive_deactivated:
                        user.status = "ACT"

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error: ", exc)
        except Exception as exc:
            db.rollback()
            print(exc)

    print("Restrict Users. Job Done")


def remove_ban_on_user_after_duration_expiration():
    db: Session = next(get_db())
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

            # get report ids
            remove_banned_report_ids = [item.report_id for item in remove_banned_users]

            # close pending appeals
            banned_users_pending_appeals = admin_service.get_all_appeals_report_id_list(
                report_id_list=remove_banned_report_ids,
                status_in_list=["OPN", "URV"],
                db_session=db,
            )
            if banned_users_pending_appeals:
                for appeal in banned_users_pending_appeals:
                    appeal.status = "CSD"
                    appeal.moderator_note = "AE"  # appeal expired

            # get user ids
            remove_banned_user_ids = [item.user_id for item in remove_banned_users]

            remove_banned_user_ids_report_ids = list(
                zip(remove_banned_user_ids, remove_banned_report_ids)
            )

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

                user_inactive_deactivated = ["DAH", "DAK", "PDH", "PDK", "INA"]
                if consecutive_violation:
                    # enforce next violation
                    consecutive_violation_query.update(
                        {"is_active": True},
                        synchronize_session=False,
                    )

                    # get user
                    user = user_service.get_user_by_id(
                        user_id=consecutive_violation.user_id,
                        status_not_in_list=["ACT", "RSP", "RSF", "PBN", "DEL"],
                        db_session=db,
                    )
                    if user:
                        consecutive_violation_operations(
                            consecutive_violation=consecutive_violation, db=db
                        )

                        # send email if status is TBN/PBN
                        if consecutive_violation.status == "PBN" or (
                            consecutive_violation.status == "TBN"
                            and user.status not in user_inactive_deactivated
                        ):
                            print("Hello")
                            # generate appeal link
                            appeal_link = (
                                "https://vpkonnect.in/accounts/appeals/form_ban"
                            )

                            email_subject = "VPKonnect - Account Ban"
                            email_details = admin_schema.SendEmail(
                                template=(
                                    "permanent_ban_email.html"
                                    if consecutive_violation.status == "PBN"
                                    else "temporary_ban_email.html"
                                ),
                                email=[EmailStr(user.email)],
                                body_info={
                                    "username": user.username,
                                    "link": appeal_link,
                                    "days": consecutive_violation.duration // 24,
                                    "ban_enforced_datetime": consecutive_violation.enforce_action_at.strftime(
                                        "%b %d, %Y %H:%M %Z"
                                    ),
                                },
                            )

                            # email_utils.send_email(
                            #     email_subject, email_details, background_tasks
                            # )

                            print("1")
                            url = "http://127.0.0.1:8000/users/send_ban_mail"
                            json_data = {
                                "email_subject": email_subject,
                                "email_details": email_details,
                            }
                            print("2")
                            requests.post(url=url, json=json_data)
                            print("3")

                        # update user status
                        if user.status not in user_inactive_deactivated or (
                            user.status in user_inactive_deactivated
                            and consecutive_violation.status == "PBN"
                        ):
                            user.status = consecutive_violation.status
                else:
                    user = user_service.get_user_by_id(
                        user_id=banned_user_id,
                        status_not_in_list=["ACT", "RSP", "RSF", "PBN", "DEL"],
                        db_session=db,
                    )
                    if user and user.status not in user_inactive_deactivated:
                        user.status = "ACT"  # status update

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error: ", exc)

    print("Ban Users. Job Done")


def user_inactivity_delete(background_tasks: BackgroundTasks):
    db: Session = next(get_db())
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

    if inactive_auth_entries:
        try:
            # change user status to PDI
            for user in inactive_auth_entries:
                user.status = "PDI"

            # revoke the restrict/ban if there's one, by changing is_active to False, since the user is to be deleted permanently, restrict/ban is meaningless after this
            users_active_restrict_ban_query.update(
                {"is_active": False},
                synchronize_session=False,
            )

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

        # get user emails
        inactive_user_emails = [user.email for user in inactive_auth_entries]

        # generate request data link
        request_data_link = "https://vpkonnect.in/accounts/data_request_form"
        email_subject = "VPKonnect - Account Deletion Due to User Inactivity"
        email_details = admin_schema.SendEmail(
            template="inactivity_delete_email.html",
            email=inactive_user_emails,
            body_info={
                "link": request_data_link,
            },
        )
        try:
            email_utils.send_email(email_subject, email_details, background_tasks)
        except Exception as exc:
            print("Email error: ", exc)

    print("Inactive Delete Users. Job Done")


def user_inactivity_inactive():
    db: Session = next(get_db())
    # get all user auth track entries whose last entry has passed 3 months, recent ones
    inactive_auth_entries = auth_service.user_auth_track_user_inactivity_inactive(
        db_session=db
    )
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
            try:
                for user in users_to_be_inactivated:
                    user.status = "INA"

                db.commit()
            except SQLAlchemyError as exc:
                db.rollback()
                print("SQL Error:", exc)

    print("Inactive Users. Job Done")


# PBN 21 day appeal limit check
def delete_user_after_permanent_ban_appeal_limit_expiry(
    background_tasks: BackgroundTasks,
):
    db: Session = next(get_db())

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
            func.now()
            >= (
                admin_model.UserRestrictBanDetail.enforce_action_at
                + timedelta(days=21),
            ),
            admin_model.UserContentRestrictBanAppealDetail.id == None,
        )
        .all()
    )

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
            user_id_list=pbn_no_appeal_user_ids, status_in_list=["PBN"], db_session=db
        )

        try:
            # update is_active to False
            for ban_entry in pbn_no_appeal_ban_entries:
                ban_entry.is_active = False

            # update user status to PDB
            for user in pbn_no_appeal_users:
                user.status = "PDB"

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

        # get user emails
        pbn_no_appeal_user_emails = [user.email for user in pbn_no_appeal_users]

        # generate request data link
        request_data_link = "https://vpkonnect.in/accounts/data_request_form"
        email_subject = "VPKonnect - Account Deletion Due to Appeal Limit Expiration"
        email_details = admin_schema.SendEmail(
            template="appeal_limit_account_delete.html",
            email=pbn_no_appeal_user_emails,
            body_info={
                "link": request_data_link,
            },
        )
        try:
            email_utils.send_email(email_subject, email_details, background_tasks)
        except Exception as exc:
            print("Email error: ", exc)

    print("PBN 21 day Appeal Limit. Job Done")


# post/comment 21 day appeal limit check
def delete_content_after_ban_appeal_limit_expiry():
    db: Session = next(get_db())

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
            func.now() >= (post_model.Post.updated_at + timedelta(days=21)),
            or_(
                admin_model.UserContentRestrictBanAppealDetail.id == None,
                admin_model.UserContentRestrictBanAppealDetail.status == "ACP",
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
            func.now() >= (comment_model.Comment.updated_at + timedelta(days=21)),
            or_(
                admin_model.UserContentRestrictBanAppealDetail.id == None,
                admin_model.UserContentRestrictBanAppealDetail.status == "ACP",
            ),
        )
        .all()
    )

    if posts_with_no_pending_appeal:
        # get all post ids of the posts to be deleted
        post_ids = [post_entry.id for post_entry in posts_with_no_pending_appeal]

        try:
            # get posts query
            posts_to_be_deleted_query = post_service.get_all_posts_by_id_query(
                post_id_list=post_ids, status_in_list=["BAN"], db_session=db
            )

            # update the is_deleted to True
            posts_to_be_deleted_query.update(
                {"is_deleted": True},
                synchronize_session=False,
            )

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

    if comments_with_no_pending_appeal:
        # get all comment ids of the posts to be deleted
        comment_ids = [
            comment_entry.id for comment_entry in comments_with_no_pending_appeal
        ]

        try:
            # get comments query
            comments_to_be_deleted_query = comment_service.get_all_comments_by_id_query(
                comment_id_list=comment_ids, status_in_list=["BAN"], db_session=db
            )

            # update the is_deleted to True
            comments_to_be_deleted_query.update(
                {"is_deleted": True},
                synchronize_session=False,
            )

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

    print("Post/Comment 21 day Appeal Limit. Job Done")


def close_appeal_after_duration_limit_expiration():
    # this is for PBN and post/comment ban appeals only
    # for RSP, RSF and TBN it is handled during removing restrict/ban job
    db: Session = next(get_db())

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
            admin_model.UserContentRestrictBanAppealDetail.status.in_(["OPN", "URV"]),
            func.now()
            >= (
                admin_model.UserContentRestrictBanAppealDetail.created_at
                + timedelta(days=30)
            ),
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

        try:
            # update appeal status and moderator_note
            for appeal in pbn_expired_pending_appeals:
                appeal.status = "CSD"
                appeal.moderator_note = "AE"  # appeal expired

            for user in pbn_expired_pending_appeal_users:
                user.status = "PDB"

            for ban_entry in pbn_expired_pending_appeal_ban_entries:
                ban_entry.is_active = False

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

    # post/comment
    # query the user_content_restrict_ban_appeal_detail for OPN/URV using content_type as post or comment
    # filter for 30 day process limit
    # change the appeal status to CSD
    # change is_deleted to True for post/comment
    pending_appeals = admin_service.get_all_appeals_content_id_list(
        content_id_list=None,
        content_type_list=["post", "comment"],
        status_in_list=["OPN", "URV"],
        db_session=db,
    )
    if pending_appeals:
        for appeal in pending_appeals:
            appeal.status = "CSD"
            appeal.moderator_note = "AE"  # appeal expired

        # get the content ids
        appealed_post_ids = {
            appeal_entry.content_id
            for appeal_entry in pending_appeals
            if appeal_entry.content_type == "post"
        }
        appealed_comment_ids = {
            appeal_entry.content_id
            for appeal_entry in pending_appeals
            if appeal_entry.content_type == "comment"
        }

        # get the posts
        appealed_posts_query = post_service.get_all_posts_by_id_query(
            post_id_list=list(appealed_post_ids), status_in_list=["BAN"], db_session=db
        )

        # get the comments
        appealed_comments_query = comment_service.get_all_comments_by_id_query(
            comment_id_list=list(appealed_comment_ids),
            status_in_list=["BAN"],
            db_session=db,
        )

        try:
            # update is_deleted to True
            appealed_posts_query.update(
                {"is_deleted": True},
                synchronize_session=False,
            )
            appealed_comments_query.update(
                {"is_deleted": True},
                synchronize_session=False,
            )
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

    print("Close Appeal. Job Done")


def reduce_violation_score_quarterly():
    # get the user ids of latest reports which are resolved, appeals for reports if any are not accepted, and are older than 3 months
    # meaning there should be no violation of user in last three months for score to reduce by 50%

    db: Session = next(get_db())

    # join user_content_report_detail and user_content_restrict_ban_appeal_detail
    report_appeal_join = (
        db.query(admin_model.UserContentReportDetail.reported_user_id)
        .join(
            admin_model.UserContentRestrictBanAppealDetail,
            admin_model.UserContentReportDetail.id
            == admin_model.UserContentRestrictBanAppealDetail.report_id,
            isOuter=True,
        )
        .filter(
            admin_model.UserContentReportDetail.status == "RSD",
            admin_model.UserContentRestrictBanAppealDetail.status.notin_(
                ["ACP", "ACR"]
            ),
            func.now()
            > (admin_model.UserContentReportDetail.updated_at + timedelta(days=91)),
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
    guideline_violation_score_entries = guideline_violation_score_entries_query.all()
    if guideline_violation_score_entries:
        try:
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
            print("SQL Error:", exc)

    print("Score Reduction. Job Done")
