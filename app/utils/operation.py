from datetime import datetime, timedelta
from uuid import UUID

import requests
from fastapi import HTTPException, status
from sqlalchemy import func

# from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import admin as admin_model
from app.services import admin as admin_service
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import log as log_utils


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error. Report concerning the consecutive violation not found",
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error. Guideline Violation Score for user not found",
        )

    last_added_score_entry = admin_service.get_last_added_score(
        score_id=str(violation_score_entry.id),
        report_id=str(consecutive_violation_report.id),
        db_session=db,
        is_added=False,
    )
    if not last_added_score_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error. Last added score concerning the report and user not found",
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error. Valid Flagged Content(s) associated with consecutive violation report not found",
            )

        valid_flagged_content_ids = [content[0] for content in valid_flagged_content]
        # we flag only posts for report type account, so content is basically post, valid_flagged_content_ids is a list of post ids
        for content_id in valid_flagged_content_ids:
            # print(content_id)
            post = post_service.get_a_post(
                post_id=str(content_id),
                status_not_in_list=["PUB", "DRF", "HID", "RMV"],
                db_session=db,
            )
            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error. Valid Flagged Post associated with consecutive violation account report not found",
                )
            if post.status == "BAN":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Error. Valid Flagged Post associated with consecutive violation account report already banned",
                )

            if post.status == "FLD":
                print("Valid Flagged Post already deleted. Status not changed to BAN")
            elif post.status == "FLB":
                post.status = "BAN"
    else:
        if consecutive_violation_report.reported_item_type == "post":
            post = post_service.get_a_post(
                post_id=str(consecutive_violation_report.reported_item_id),
                status_not_in_list=["PUB", "DRF", "HID", "RMV"],
                db_session=db,
            )
            if not post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error. Post associated with consecutive violation report not found",
                )
            if post.status == "BAN":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Error. Post associated with consecutive violation report already banned",
                )

            if post.status == "FLD":
                print("Flagged Post already deleted. Status not changed to BAN")
            elif post.status == "FLB":
                post.status = "BAN"

        elif consecutive_violation_report.reported_item_type == "comment":
            comment = comment_service.get_a_comment(
                comment_id=str(consecutive_violation_report.reported_item_id),
                status_not_in_list=["PUB", "HID", "RMV"],
                db_session=db,
            )
            if not comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Error. Comment associated with consecutive violation report not found",
                )
            if comment.status == "BAN":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Error. Comment associated with consecutive violation report already banned",
                )

            if comment.status == "FLD":
                print("Flagged Comment already deleted. Status not changed to BAN")
            elif comment.status == "FLB":
                comment.status = "BAN"


def user_restrict_ban_detail_user_operation(
    user_id: UUID,
    report_id: UUID,
    restrict_status: str,
    db: Session,
):
    current_entry = admin_service.get_user_active_restrict_ban_entry_user_id_report_id(
        user_id=str(user_id),
        status=restrict_status,
        report_id=str(report_id),
        db_session=db,
    )
    if not current_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active restrict/ban entry to remove restrict/ban not found",
        )

    # remove the current restrict/ban
    current_entry.is_active = False

    # get user
    user = user_service.get_user_by_id(
        user_id=str(user_id),
        status_not_in_list=["ACT", "PDI", "PDB", "DEL"],
        db_session=db,
    )

    consecutive_violation = None
    send_mail = False
    if user:
        # subquery to get the next nearest enforce_action_at which is greater than now(), scalar is used to directly fetch the value of single column value from the query
        subq_min_enforce_action_at = (
            db.query(func.min(admin_model.UserRestrictBanDetail.enforce_action_at))
            .filter(
                admin_model.UserRestrictBanDetail.user_id == user_id,
                admin_model.UserRestrictBanDetail.report_id
                != report_id,  # exclude the current deactivated restrict/ban entry
                admin_model.UserRestrictBanDetail.enforce_action_at > func.now(),
                admin_model.UserRestrictBanDetail.is_active == False,
                admin_model.UserRestrictBanDetail.is_deleted == False,
            )
            .scalar()
        )

        # print(subq_min_enforce_action_at)
        consecutive_violation_query = db.query(
            admin_model.UserRestrictBanDetail
        ).filter(
            admin_model.UserRestrictBanDetail.user_id == user_id,
            admin_model.UserRestrictBanDetail.enforce_action_at
            == subq_min_enforce_action_at,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )

        consecutive_violation = consecutive_violation_query.first()

        user_inactive_deactivated = ["DAH", "PDH", "INA"]
        if consecutive_violation:
            # enforce next violation, this will be early enforce
            consecutive_violation_query.update(
                {
                    "is_active": True,
                    "enforce_action_at": func.now(),
                    "is_enforce_action_early": True,
                },
                synchronize_session=False,
            )

            consecutive_violation_operations(
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
                # # generate appeal link
                # appeal_link = "https://vpkonnect.in/accounts/appeals/form_ban"

                # email_subject = "VPKonnect - Account Ban"
                # email_details = admin_schema.SendEmail(
                #     template=(
                #         "permanent_ban_email.html"
                #         if consecutive_violation.status == "PBN"
                #         else "temporary_ban_email.html"
                #     ),
                #     email=[EmailStr(user.email)],
                #     body_info={
                #         "username": user.username,
                #         "link": appeal_link,
                #         "days": consecutive_violation.duration // 24,
                #         "ban_enforced_datetime": consecutive_violation.enforce_action_at.strftime(
                #             "%b %d, %Y %H:%M %Z"
                #         ),
                #     },
                # )
                send_mail = True
        else:
            if user.status not in user_inactive_deactivated:
                user.status = "ACT"

    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with restrict/ban not found",
        )

    return consecutive_violation, send_mail


def guideline_violation_score_last_added_score_operation(
    user_id: UUID,
    report_id: UUID,
    ban_content_type: str,
    db: Session,
    content_to_be_unbanned: int,
    content_already_unbanned: int,
    account_report_flagged_content: int | None = None,
):
    # get guideline violation score entry
    guideline_violation_score_entry_query = (
        admin_service.get_user_guideline_violation_score_query(
            user_id=str(user_id), db_session=db
        )
    )
    guideline_violation_score_entry = guideline_violation_score_entry_query.first()
    if not guideline_violation_score_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guideline violation score entry for updating scores of user not found",
        )

    # get last_added_score from guideline_violation_last_added_score
    last_added_score_entry = admin_service.get_last_added_score(
        score_id=guideline_violation_score_entry.id,
        report_id=str(report_id),
        db_session=db,
    )
    if not last_added_score_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Error. Last added score entry of restrict/ban not found",
        )

    # set the score_type and get curr_score for the content type
    if ban_content_type == "post":
        score_type = "post_score"
        curr_score = guideline_violation_score_entry.post_score
    elif ban_content_type == "comment":
        score_type = "comment_score"
        curr_score = guideline_violation_score_entry.comment_score
    elif ban_content_type == "message":
        score_type = "message_score"
        curr_score = guideline_violation_score_entry.message_score
    # if reported item type is account, then use post_score, as posts reflect most of the account
    else:
        score_type = "post_score"
        curr_score = guideline_violation_score_entry.post_score

    last_added_score = last_added_score_entry.last_added_score
    curr_final_violation_score = guideline_violation_score_entry.final_violation_score

    # for account report cases, where many flagged posts are involved, some posts unbanned through different appeals, some remain unbanned or not unbanned at all
    # So only the fraction of last_added_score will be considered
    if account_report_flagged_content:
        effective_last_added_score = int(
            (content_to_be_unbanned / account_report_flagged_content) * last_added_score
        )
    else:
        effective_last_added_score = last_added_score

    # adjust the scores (appropriate content score and final violation score)
    # if scores after adjustment goes -ve, make it 0
    diff_score = max(curr_score - effective_last_added_score, 0)
    new_final_violation_score = max(
        curr_final_violation_score - effective_last_added_score, 0
    )

    # update is_removed to True only if last added score is completely considered to adjust violation scores
    # report type is account and either all posts got unbanned or last post of the valid flagged content list got unbanned
    # OR report type is post/comment
    # only in these conditions the last added score is_removed is made True
    if (
        ban_content_type == "account"
        and (
            content_already_unbanned + content_to_be_unbanned
            == account_report_flagged_content
        )
    ) or (ban_content_type in ("post", "comment")):
        last_added_score_entry.is_removed = True

    guideline_violation_score_entry_query.update(
        {
            score_type: diff_score,
            "final_violation_score": new_final_violation_score,
        },
        synchronize_session=False,
    )


def post_comment_operation(ban_content_id: UUID, ban_content_type: str, db: Session):
    if ban_content_type == "post":
        # get post
        post_entry = post_service.get_a_post(
            post_id=str(ban_content_id),
            status_not_in_list=["PUB", "DRF", "HID", "FLD", "FLB", "RMV"],
            db_session=db,
        )
        if not post_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post to be unbanned not found",
            )

        # update status to PUB
        post_entry.status = "PUB"

    if ban_content_type == "comment":
        # get comment
        comment_entry = comment_service.get_a_comment(
            comment_id=str(ban_content_id),
            status_not_in_list=["PUB", "HID", "FLD", "FLB", "RMV"],
            db_session=db,
        )
        if not comment_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment to be unbanned not found",
            )

        # update status to PUB
        comment_entry.status = "PUB"


def operations_after_appeal_accept(
    user_id: UUID,
    report_id: UUID,
    appeal_content_id: UUID,
    appeal_content_type: str,
    restrict_ban_content_id: UUID | None,
    restrict_ban_content_type: str | None,
    restrict_ban_status: str | None,
    restrict_ban_is_active: bool | None,
    db: Session,
):
    send_mail = None
    consecutive_violation = None

    if appeal_content_type == "account":
        print("Account")
        # Appeal type: account, Report type: account
        if restrict_ban_content_type == "account":
            print("Account-Account")
            # fetch the flagged posts from account_report_flagged_content, get all or partial no of posts which are banned, change the status from BAN to PUB
            # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
            # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
            account_report_valid_flagged_content = (
                admin_service.get_all_valid_flagged_content_account_report_id(
                    report_id=report_id, db_session=db
                )
            )
            account_report_flagged_content_ids = [
                content[0] for content in account_report_valid_flagged_content
            ]
            no_of_flagged_posts = len(account_report_flagged_content_ids)

            account_report_flagged_posts = post_service.get_all_posts_by_id_query(
                post_id_list=account_report_flagged_content_ids,
                status_in_list=["BAN"],
                db_session=db,
            ).all()
            no_of_banned_posts = len(account_report_flagged_posts)

            for post in account_report_flagged_posts:
                post.status = "PUB"

            guideline_violation_score_last_added_score_operation(
                user_id=user_id,
                report_id=report_id,
                ban_content_type=restrict_ban_content_type,
                db=db,
                account_report_flagged_content=no_of_flagged_posts,
                content_to_be_unbanned=no_of_banned_posts,
                content_already_unbanned=(no_of_flagged_posts - no_of_banned_posts),
            )

            consecutive_violation, send_mail = user_restrict_ban_detail_user_operation(
                user_id=user_id,
                report_id=report_id,
                restrict_status=restrict_ban_status,
                db=db,
            )

        # Appeal type: account, Report type: post/comment
        elif restrict_ban_content_type in (
            "post",
            "comment",
        ):
            # fetch the banned post/comment and change the status to PUB
            # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
            # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
            post_comment_operation(
                ban_content_id=restrict_ban_content_id,
                ban_content_type=restrict_ban_content_type,
                db=db,
            )

            guideline_violation_score_last_added_score_operation(
                user_id=user_id,
                report_id=report_id,
                ban_content_type=restrict_ban_content_type,
                db=db,
                content_to_be_unbanned=1,
                content_already_unbanned=0,
            )

            consecutive_violation, send_mail = user_restrict_ban_detail_user_operation(
                user_id=user_id,
                report_id=report_id,
                restrict_status=restrict_ban_status,
                db=db,
            )

    elif appeal_content_type in (
        "post",
        "comment",
    ):
        if appeal_content_type == "post" and restrict_ban_content_type == "account":
            # fetch the flagged posts from account_report_flagged_content
            # fetch the appealed post, change the status to PUB
            # If all posts have their bans revoked then consider last added score and manage it, update is_removed to True
            # *** consider revoking restrict when last post is getting unbanned

            #     Else consider only fraction of last added score
            # update guideline violation score table

            account_report_valid_flagged_content = (
                admin_service.get_all_valid_flagged_content_account_report_id(
                    report_id=report_id, db_session=db
                )
            )
            account_report_flagged_content_ids = [
                content[0] for content in account_report_valid_flagged_content
            ]
            no_of_flagged_posts = len(account_report_flagged_content_ids)

            account_report_flagged_posts = post_service.get_all_posts_by_id_query(
                post_id_list=account_report_flagged_content_ids,
                status_in_list=["PUB"],
                db_session=db,
            ).all()
            no_of_posts_already_unbanned = len(account_report_flagged_posts)

            post_comment_operation(
                ban_content_id=appeal_content_id,
                ban_content_type=appeal_content_type,
                db=db,
            )

            guideline_violation_score_last_added_score_operation(
                user_id=user_id,
                report_id=report_id,
                ban_content_type=restrict_ban_content_type,
                db=db,
                content_to_be_unbanned=1,
                content_already_unbanned=no_of_posts_already_unbanned,
                account_report_flagged_content=no_of_flagged_posts,
            )

            # Appeal type: post, Report type: account (active restrict)
            if restrict_ban_is_active == "True":
                # check if all the flagged posts have PUB status, if yes then revoke the restrict, else don't
                # if restrict is revoked, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status
                if (no_of_posts_already_unbanned + 1) == no_of_flagged_posts:
                    consecutive_violation, send_mail = (
                        user_restrict_ban_detail_user_operation(
                            user_id=user_id,
                            report_id=report_id,
                            restrict_status=restrict_ban_status,
                            db=db,
                        )
                    )

            # Appeal type: post, Report type: account (inactive restrict/ban)
            elif restrict_ban_is_active == "False":
                # all required operations are done before
                pass

        elif restrict_ban_content_type in (
            "post",
            "comment",
        ):
            # fetch the banned post/comment, update status to PUB
            post_comment_operation(
                ban_content_id=restrict_ban_content_id,
                ban_content_type=restrict_ban_content_type,
                db=db,
            )

            # Appeal type: post/comment, Report type: post/comment (active restrict)
            if restrict_ban_is_active == "True":
                # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                # revoke the active restrict/ban, activate consecutive violation if any (set enforce_action_at with func.now() and is_enforce_action_early as True), update user status

                guideline_violation_score_last_added_score_operation(
                    user_id=user_id,
                    report_id=report_id,
                    ban_content_type=restrict_ban_content_type,
                    db=db,
                    content_to_be_unbanned=1,
                    content_already_unbanned=0,
                )

                consecutive_violation, send_mail = (
                    user_restrict_ban_detail_user_operation(
                        user_id=user_id,
                        report_id=report_id,
                        restrict_status=restrict_ban_status,
                        db=db,
                    )
                )

            # Appeal type: post/comment, Report type: post/comment (active restrict/ban concluded)
            elif restrict_ban_is_active == "False":
                # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
                guideline_violation_score_last_added_score_operation(
                    user_id=user_id,
                    report_id=report_id,
                    ban_content_type=restrict_ban_content_type,
                    db=db,
                    content_to_be_unbanned=1,
                    content_already_unbanned=0,
                )
        # Appeal type: post/comment, Report type: post/comment (No restrict/ban associated)
        elif not restrict_ban_content_type:
            # fetch the banned post/comment, update status to PUB
            # adjust the scores in guideline violation score table, fetch last added score from guideline violation last added score table and update is_removed to true
            post_comment_operation(
                ban_content_id=appeal_content_id,
                ban_content_type=appeal_content_type,
                db=db,
            )

            guideline_violation_score_last_added_score_operation(
                user_id=user_id,
                report_id=report_id,
                ban_content_type=appeal_content_type,
                db=db,
                content_to_be_unbanned=1,
                content_already_unbanned=0,
            )

    return consecutive_violation, send_mail


def operations_after_appeal_reject(
    user_id: UUID,
    report_id: UUID,
    appeal_content_id: UUID,
    appeal_content_type: str,
    restrict_ban_content_id: UUID | None,
    restrict_ban_content_type: str | None,
    restrict_ban_status: str | None,
    restrict_ban_enforce_action_at: datetime | None,
    db: Session,
):
    if appeal_content_type == "account":
        if restrict_ban_content_type == "account":
            # common for RSP, RSF, TBN and PBN
            # get all valid flagged content posts
            valid_flagged_content_posts = (
                admin_service.get_all_valid_flagged_content_account_report_id(
                    report_id=report_id, db_session=db
                )
            )
            if not valid_flagged_content_posts:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Valid flagged content posts associated with account report not found",
                )

            # get post ids
            valid_flagged_content_posts_ids = [
                post[0] for post in valid_flagged_content_posts
            ]

            # get the posts
            posts_to_be_banned_final = post_service.get_all_posts_by_id_query(
                post_id_list=valid_flagged_content_posts_ids,
                status_in_list=["BAN"],
                db_session=db,
            ).all()
            if not posts_to_be_banned_final:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Posts whose ban is to be finalised not found",
                )

            # update is_ban_final to True
            for post in posts_to_be_banned_final:
                post.is_ban_final = True

            # reject after 21 days appeal limit, PBN becomes PDB
            if restrict_ban_status == "PBN":
                if func.now() > restrict_ban_enforce_action_at + timedelta(
                    days=settings.pbn_appeal_submit_limit_days
                ):
                    # get the ban entry
                    ban_entry = (
                        admin_service.get_user_active_restrict_ban_entry_report_id(
                            report_id=report_id, db_session=db
                        )
                    )
                    if not ban_entry:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ban entry associated with rejected appeal for PBN not found",
                        )

                    # get the PBN user
                    pbn_appeal_reject_user_query = user_service.get_user_by_id_query(
                        user_id=str(user_id),
                        status_not_in_list=[
                            "ACT",
                            "INA",
                            "RSP",
                            "RSF",
                            "TBN",
                            "PDB",
                            "PDI",
                            "DAH",
                            "PDH",
                            "DEL",
                        ],
                        db_session=db,
                    )

                    pbn_appeal_reject_user_query.update(
                        {"status": "PDB"},
                        synchronize_session=False,
                    )

                    # revoke the ban
                    ban_entry.is_active = False
        elif restrict_ban_content_type in ("post", "comment"):
            if restrict_ban_content_type == "post":
                appeal_reject_post = post_service.get_a_post(
                    post_id=str(restrict_ban_content_id),
                    status_not_in_list=["PUB", "DRF", "HID", "RMV", "FLB", "FLD"],
                    db_session=db,
                )
                if not appeal_reject_post:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post associated with rejected appeal not found",
                    )

                # update is_ban_final to True
                appeal_reject_post.is_ban_final = True

            elif restrict_ban_content_type == "comment":
                appeal_reject_comment = comment_service.get_a_comment(
                    comment_id=str(restrict_ban_content_id),
                    status_not_in_list=["PUB", "HID", "RMV", "FLB", "FLD"],
                    db_session=db,
                )
                if not appeal_reject_comment:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Comment associated with rejected appeal not found",
                    )

                # update is_ban_final to True
                appeal_reject_comment.is_ban_final = True

    elif appeal_content_type in ("post", "comment"):
        # appeal type post/comment, report type account
        if restrict_ban_content_type == "account":
            # check if content id is present in valid flagged posts or not
            content_in_valid_flagged_content = admin_service.get_account_report_flagged_content_entry_valid_flagged_content_id_report_id(
                content_id=appeal_content_id, report_id=report_id, db_session=db
            )

            if not content_in_valid_flagged_content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appealed content id not found in account report valid flagged content list",
                )

            # get that post
            appeal_reject_post = post_service.get_a_post(
                post_id=str(appeal_content_id),
                status_not_in_list=["PUB", "DRF", "HID", "RMV", "FLB", "FLD"],
                db_session=db,
            )
            if not appeal_reject_post:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Post associated with rejected appeal not found",
                )

            # update is_ban_final to True
            appeal_reject_post.is_ban_final = True

        # appeal type post/comment and report type post/comment
        elif restrict_ban_content_type in ("post", "comment"):
            if restrict_ban_content_type == "post":
                appeal_reject_post = post_service.get_a_post(
                    post_id=str(appeal_content_id),
                    status_not_in_list=["PUB", "DRF", "HID", "RMV", "FLB", "FLD"],
                    db_session=db,
                )
                if not appeal_reject_post:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Post associated with rejected appeal not found",
                    )

                # update is_ban_final to True
                appeal_reject_post.is_ban_final = True

            elif restrict_ban_content_type == "comment":
                appeal_reject_comment = comment_service.get_a_comment(
                    comment_id=str(appeal_content_id),
                    status_not_in_list=["PUB", "HID", "RMV", "FLB", "FLD"],
                    db_session=db,
                )
                if not appeal_reject_comment:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Comment associated with rejected appeal not found",
                    )

                # update is_ban_final to True
                appeal_reject_comment.is_ban_final = True
