from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import admin as admin_model
from app.services import admin as admin_service
from app.services import auth as auth_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service


def delete_user_after_deactivation_period_expiration():
    db: Session = next(get_db())
    # get all delete schedule duration expiry entries
    scheduled_delete_entries = (
        user_service.check_deactivation_expiration_for_scheduled_delete(db_session=db)
    )
    # print(scheduled_delete_entries[0].__dict__ if scheduled_delete_entries else None)
    if scheduled_delete_entries:
        # fetch user ids
        scheduled_delete_user_ids = [
            str(user.user_id) for user in scheduled_delete_entries
        ]
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
        valid_flagged_content = admin_service.get_valid_flagged_content_account_report(
            report_id=str(consecutive_violation_report.id), db_session=db
        )
        if not valid_flagged_content:
            raise Exception(
                "Error. Valid Flagged Content(s) associated with consecutive violation report not found"
            )

        # we flag only posts for report type account, so content is basically post, valid_flagged_content is a list of post ids
        for content in valid_flagged_content[0]:
            print(content)
            post = post_service.get_a_post(
                post_id=str(content),
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


def remove_restriction_on_user_after_duration_expiration():
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
                        str(consecutive_violation.user_id), ["ACT", "PBN", "DEL"], db
                    )
                    if user and user.status not in ["DAH", "DAK", "PDH", "PDK", "INA"]:
                        user.status = consecutive_violation.status  # status update

                    consecutive_violation_operations(
                        consecutive_violation=consecutive_violation, db=db
                    )

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

                    consecutive_violation_operations(
                        consecutive_violation=consecutive_violation, db=db
                    )
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


def user_inactivity_delete():
    db: Session = next(get_db())
    # get all user auth track entries whose last entry has passed 6 months, recent ones
    inactive_auth_entries = auth_service.user_auth_track_user_inactivity_delete(
        db_session=db
    )
    if inactive_auth_entries:
        try:
            for user in inactive_auth_entries:
                user.status = "PDI"

            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            print("SQL Error:", exc)

    print("Inactive Delete Users. Done")


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

    print("Inactive Users. Done")


# def reduce_violation_score_quarterly(db_session = next(get_db())):
#     # get the user ids of latest reports which are resolved, appeals for reports if any are not accepted, and are older than 3 months
#     # meaning there should be no violation of user in last three months for score to reduce by 25%
