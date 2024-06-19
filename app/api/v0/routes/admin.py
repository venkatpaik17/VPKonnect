from datetime import date, datetime, timedelta, timezone
from math import floor, inf
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, status
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import admin as admin_model
from app.schemas import admin as admin_schema
from app.schemas import auth as auth_schema
from app.services import admin as admin_service
from app.services import comment as comment_service
from app.services import employee as employee_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import email as email_utils
from app.utils import map as map_utils

router = APIRouter(prefix=settings.api_prefix + "/admin", tags=["Admin"])


# get all reports (open/under review)
@router.get("/reports", response_model=list[admin_schema.AllReportResponse])
def get_reported_items(
    report_status: str = Form(),
    moderator_emp_id: str = Form(
        None
    ),  # for curr emp it will be None, for other emp it will be emp_id, for all emps it will be 'all'
    date_reported: date = Form(None),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # create request object
    get_reports_request = admin_schema.AllReportRequest(
        status=report_status, emp_id=moderator_emp_id, reported_at=date_reported
    )

    # get current employee
    curr_moderator_employee = employee_service.get_employee_by_work_email(
        str(current_employee.email), db
    )

    # get request moderator employee
    request_moderator = None
    # emp_id is None, so curr_moderator_employee is the request_moderator
    if not get_reports_request.emp_id:
        request_moderator = curr_moderator_employee
    # all means, do not use emp_id as filter, hence request_moderator is None
    elif get_reports_request.emp_id == "all":
        request_moderator = None
    # if emp_id is given then fetch that moderator
    else:
        request_moderator = employee_service.get_employee_by_emp_id(
            get_reports_request.emp_id, db
        )
        if not request_moderator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Requested employee not found",
            )

    moderator_id = None
    # set all parameters for getting all reports based on status
    if get_reports_request.status == "OPN":
        moderator_id = None
    elif get_reports_request.status in ["URV", "CSD", "RSD"]:
        # request_moderator will be either curr_moderator_employee or requested moderator
        moderator_id = request_moderator.id if request_moderator else None
    elif get_reports_request.status == "all":
        moderator_id = None or (request_moderator.id if request_moderator else None)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid report status"
        )

    # fetch all reports, all_reports is a list of UserConterntReportDetail objects
    all_reports = admin_service.get_all_reports_by_status_moderator_id_reported_at(
        get_reports_request.status,
        db,
        moderator_id,
        get_reports_request.reported_at,
    )
    # print(all_reports[0].reported_user.__dict__)

    # loop through all UserConterntReportDetail objects in all_reports, get required parameters
    # prepare the response object (list of admin_schema.AllReportResponse objects)
    all_reports_response = []
    for report in all_reports:
        all_reports_response.append(
            admin_schema.AllReportResponse(
                case_number=report.case_number,
                status=report.status,
                reported_at=report.created_at,
            )
        )
    # print(all_reports_response)

    return all_reports_response


# reports dashboard
@router.get(
    "/reports/{report_status}", response_model=list[admin_schema.AllReportResponse]
)
def get_reports_dashboard(
    report_status: str,
    moderator_emp_id: str,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get curr employee
    curr_moderator_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email), db_session=db
    )

    # check identity
    if curr_moderator_employee.emp_id != moderator_emp_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to peform requested action",
        )

    # get reports based on status and moderator
    all_reports = admin_service.get_all_reports_by_status_moderator_id_reported_at(
        status=report_status,
        moderator_id=curr_moderator_employee.moderator_id,
        reported_at=None,
        db_session=db,
    )

    all_reports_response = None
    if all_reports:
        all_reports_response = [
            admin_schema.AllReportResponse(
                case_number=report.case_number,
                status=report.status,
                reported_at=report.created_at,
            )
            for report in all_reports
        ]

    return all_reports_response


# get a report
@router.get("/reports/{case_number}")
def get_requested_report(
    case_number: int,
    report_request: admin_schema.ReportRequest,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get current employee__dict__
    curr_moderator_employee = employee_service.get_employee_by_work_email(
        str(current_employee.email), db
    )

    # get the report
    requested_report = admin_service.get_a_report(
        case_number, report_request.status, db
    )
    if not requested_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
        )

    # for account type and status RSD/RSR/FRS/FRR, we need to fetch the flagged/banned posts
    flagged_banned_posts_ids = []
    if (
        requested_report.reported_item_type == "account"
        and requested_report.status in ("RSD, RSR, FRS, FRR")
    ):
        flagged_banned_posts = (
            admin_service.get_all_valid_flagged_content_account_report_id(
                report_id=requested_report.id, db_session=db
            )
        )
        if not flagged_banned_posts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flagged/Banned posts associated with account report not found",
            )

        flagged_banned_posts_ids = [post[0] for post in flagged_banned_posts]

    # get the required objects (User, Post, Comment) and other parameters
    # prepare the response object
    # report_response = admin_schema.ReportResponse(
    #     reporter_user=requested_report.reporter_user.__dict__,
    #     reported_user=requested_report.reported_user.__dict__,
    #     reported_item_type=requested_report.reported_item_type,
    #     reported_item=(
    #         (requested_report.post.__dict__ if requested_report.post else None)
    #         or (requested_report.comment.__dict__ if requested_report.comment else None)
    #         or requested_report.account.__dict__
    #     ),
    #     case_number=requested_report.case_number,
    #     report_reason=map_utils.report_reasons_code_dict.get(requested_report.report_reason),  # type: ignore
    #     report_reason_user=(
    #         requested_report.report_reason_user.__dict__
    #         if requested_report.report_reason_user
    #         else None
    #     ),
    #     status=requested_report.status,
    #     moderator_note=requested_report.moderator_note,
    #     moderator=(
    #         requested_report.moderator.__dict__ if requested_report.moderator else None
    #     ),
    #     reported_at=requested_report.created_at,
    # )

    # we create the dict and then parse it using overriding parse_obj function on ReportResponse schema
    requested_report_data = {
        "reporter_user": requested_report.reporter_user.__dict__,
        "reported_user": requested_report.reported_user.__dict__,
        "reported_item_type": requested_report.reported_item_type,
        "reported_item": (
            (requested_report.post.__dict__ if requested_report.post else None)
            or (requested_report.comment.__dict__ if requested_report.comment else None)
            or requested_report.account.__dict__
        ),
        "flagged_banned_posts": flagged_banned_posts_ids,
        "case_number": requested_report.case_number,
        "report_reason": map_utils.report_reasons_code_dict.get(
            requested_report.report_reason
        ),
        "report_reason_user": (
            requested_report.report_reason_user.__dict__
            if requested_report.report_reason_user
            else None
        ),
        "status": requested_report.status,
        "moderator_note": requested_report.moderator_note,
        "moderator": (
            requested_report.moderator.__dict__ if requested_report.moderator else None
        ),
        "reported_at": requested_report.created_at,
    }

    return admin_schema.ReportResponse.parse_obj(requested_report_data)


# get all other open reports related to a particular content report
@router.get(
    "/reports/{case_number}/related",
    response_model=list[admin_schema.AllReportResponse],
)
def get_all_related_open_reports_for_specific_report(
    case_number: int,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get the report using case_number (OPN or URV, sometimes we may need to check OPN reports for a URV report too)
    specific_report = admin_service.get_a_report(
        case_number, "OPN", db
    ) or admin_service.get_a_report(case_number, "URV", db)
    if not specific_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Specific report not found"
        )

    # get other reports
    all_other_reports = admin_service.get_open_reports_for_specific_content_report(
        specific_report.case_number,
        specific_report.reported_item_id,
        specific_report.reported_item_type,
        db,
    )

    # loop through the list of UserContentReportDetail objects and get required params
    # create response object
    all_other_reports_response = []
    for report in all_other_reports:
        all_other_reports_response.append(
            admin_schema.AllReportResponse(
                case_number=report.case_number,
                status=report.status,
                reported_at=report.created_at,
            )
        )

    return all_other_reports_response


# select reports to review
@router.patch("/reports/under-review")
def selected_reports_under_review_update(
    reports_request: admin_schema.ReportUnderReviewUpdate,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get current employee
    curr_moderator_employee = employee_service.get_employee_by_work_email(
        str(current_employee.email), db
    )

    # check if each report to be marked for review exists or not, are they open are not
    # update the valid reports
    valid_reports = []
    invalid_reports = []
    for case_no in reports_request.case_number_list:
        get_report_query = admin_service.get_a_report_query(case_no, "OPN", db)
        get_report = get_report_query.first()
        # print(get_report.__dict__)
        if not get_report:
            invalid_reports.append(case_no)
        else:
            get_report_query.update(
                {"status": "URV", "moderator_id": curr_moderator_employee.id},
                synchronize_session=False,
            )
            valid_reports.append(case_no)

    db.commit()

    if invalid_reports:
        return {
            "message": f"{len(valid_reports)} report(s) is/are marked for review",
            "error": f"{len(invalid_reports)} report(s), case number(s): {invalid_reports} could not be marked for review due to internal error. These reports might already be reviewed or are closed/resolved by concerned moderators",
        }

    return {
        "message": f"{len(valid_reports)} report(s) {valid_reports} is/are marked for review"
    }


# violation enforcement action algorithm, we use this only for post, comment and message reports
# for account reports, use manual action
@router.post("/reports/action/auto")
def enforce_report_action_auto(
    action_request: admin_schema.EnforceReportActionAuto,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email), db_session=db
    )

    # check identity
    if curr_employee and (action_request.moderator_emp_id != curr_employee.emp_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # get the report from case number
    report_query = admin_service.get_a_report_query(
        action_request.case_number, "URV", db
    )
    report = report_query.first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report to be taken action on, not found",
        )

    # check if the content exists or not
    if report.reported_item_type == "account":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested action cannot be performed. Please use Manual Action",
        )

    elif report.reported_item_type == "post":
        post_query = post_service.get_a_post_query(
            str(report.reported_item_id), ["DRF", "DEL", "FLD"], db
        )
        post = post_query.first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reported post not found"
            )
        if post.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported post already banned",
            )
        if post.status == "FLB":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported post already flagged to be banned",
            )

    elif report.reported_item_type == "comment":
        comment_query = comment_service.get_a_comment_query(
            str(report.reported_item_id), ["DEL"], db
        )
        comment = comment_query.first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported comment not found",
            )
        if comment.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported comment already banned",
            )
        if comment.status == "FLB":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported comment already flagged to be banned",
            )

    # get reported user
    reported_user_query = user_service.get_user_by_username_query(
        str(action_request.reported_username), ["PBN", "DEL"], db
    )
    reported_user = reported_user_query.first()
    if not reported_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user_deactivated_inactive = False
    if reported_user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
        "INA",
    ]:
        user_deactivated_inactive = True

        # raise HTTPException(
        #     status_code=status.HTTP_404_NOT_FOUND,
        #     detail="User profile not found",
        # )

    # if there are any OPN related report(s) which were not noticed before, put it/them under review and consider it/them in this action request
    # get open related reports
    open_related_reports_to_be_reviewed = (
        admin_service.get_open_reports_for_specific_content_report(
            case_number=action_request.case_number,
            reported_item_id=report.reported_item_id,
            reported_item_type=report.reported_item_type,
            db_session=db,
        )
    )
    # get case numbers of the related reports if any
    open_related_reports_put_under_review_message = None
    if open_related_reports_to_be_reviewed:
        open_related_reports_case_numbers = [
            related_report.case_number
            for related_report in open_related_reports_to_be_reviewed
        ]
        if open_related_reports_case_numbers:
            selected_reports_under_review_update(
                reports_request=admin_schema.ReportUnderReviewUpdate(
                    case_number_list=open_related_reports_case_numbers
                ),
                db=db,
                current_employee=current_employee,
            )

            open_related_reports_put_under_review_message = f"Additional {len(open_related_reports_case_numbers)} related report(s), case number(s): {open_related_reports_case_numbers} was/were put under review and was/were included in this action request"

    # map report reason to severity group
    severity_group = map_utils.report_reasons_severity_group_dict.get(
        report.report_reason
    )
    if not severity_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Severity group not found"
        )

    if severity_group == "CMD":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested action cannot be performed. Please use Manual Action",
        )

    # map severity group to severity score
    severity_score = map_utils.severity_groups_scores_dict.get(severity_group)
    if not severity_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Severity score not found"
        )

    # map content type to weights
    content_weight = map_utils.content_weigths_dict.get(report.reported_item_type)
    if not content_weight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Content weight not found"
        )

    # fetch the current final violation score
    user_guideline_violation_score_query = (
        admin_service.get_user_guideline_violation_score_query(
            str(reported_user.id), db
        )
    )
    user_guideline_violation_score = user_guideline_violation_score_query.first()
    if not user_guideline_violation_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User guideline violation score entry not found",
        )

    curr_final_violation_score = int(
        user_guideline_violation_score.final_violation_score
    )

    # calculate new final violation score
    effective_score = floor(content_weight * severity_score)
    new_final_violation_score = curr_final_violation_score + effective_score

    no_action = False
    violation_status = ""
    violation_duration = 0
    # if the score has not changed, then no action/duration, especially for minimal
    if curr_final_violation_score == new_final_violation_score:
        no_action = True
    else:
        action_duration = tuple(
            map_utils.get_action_duration_final_violation_score(
                new_final_violation_score
            )
        )
        violation_status = str(action_duration[0])
        violation_duration = int(action_duration[1])

        if violation_status == "UND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No action found"
            )
        elif violation_status == "NA":
            no_action = True

    # set the score_type and get curr_score for the content type
    score_type = None
    curr_score = None
    if report.reported_item_type == "post":
        score_type = "post_score"
        curr_score = user_guideline_violation_score.post_score
    elif report.reported_item_type == "comment":
        score_type = "comment_score"
        curr_score = user_guideline_violation_score.comment_score
    else:
        score_type = "message_score"
        curr_score = user_guideline_violation_score.message_score

    # For no action, update user_content_report_detail, user_content_report_event_timeline using trigger and guideline_violation_score, guideline_violation_last_added_score tables
    # For action, update user_restrict_ban_detail, user_content_report_detail
    # If active action then update user_content_report_event_timeline using trigger, guideline_violation_score, guideline_violation_last_added_score and user tables
    # so updating user_content_report_detail, user_content_report_event_timeline using trigger and guideline_violation_score tables are common operations for both
    # also another common operation is to handle other under review reports if any, related to this content report, they need to be closed.
    message = ""
    new_user_restrict_ban = None
    is_active = None
    enforce_action_at = None

    if no_action:
        message = f"Request processed successfully. Report case number {action_request.case_number} resolved."

    else:
        # get all restrict/ban entries for a user
        user_all_restrict_ban_query = admin_service.get_all_user_restrict_ban_query(
            reported_user.id, db
        )

        # check if there is any active restriction/ban
        user_active_restrict_ban = user_all_restrict_ban_query.filter(
            admin_model.UserRestrictBanDetail.is_active == True
        ).first()

        # check if there is/are any consecutive restrictions/bans already in line, in those get the latest one
        user_future_restrict_ban = (
            user_all_restrict_ban_query.filter(
                admin_model.UserRestrictBanDetail.enforce_action_at > func.now(),
                admin_model.UserRestrictBanDetail.is_active == False,
                admin_model.UserRestrictBanDetail.is_deleted == False,
            )
            .order_by(admin_model.UserRestrictBanDetail.enforce_action_at.desc())
            .first()
        )

        # there is a active restrict/ban and also there is/are future restricts/bans in line
        if user_active_restrict_ban and user_future_restrict_ban:
            enforce_time = user_future_restrict_ban.enforce_action_at + timedelta(
                hours=user_future_restrict_ban.duration,
            )
            is_active = False
            enforce_action_at = enforce_time

        # there is a active restrict/ban and also there is/are no future restricts/bans in line
        elif user_active_restrict_ban and not user_future_restrict_ban:
            enforce_time = user_active_restrict_ban.enforce_action_at + timedelta(
                hours=user_active_restrict_ban.duration,
            )
            is_active = False
            enforce_action_at = enforce_time

        # no active restrict/ban
        elif not user_active_restrict_ban:
            is_active = True
            enforce_action_at = func.now()

        new_user_restrict_ban = admin_model.UserRestrictBanDetail(
            status=violation_status,
            duration=violation_duration,
            user_id=reported_user.id,
            is_active=is_active,
            content_type=report.reported_item_type,
            content_id=report.reported_item_id,
            report_id=report.id,
            enforce_action_at=enforce_action_at,
        )

        try:
            # add restrict/ban entry
            db.add(new_user_restrict_ban)

            # update user status in user table only if action is enforced now i.e is_active = True and (user is not deactivated/inactive or user is deactivated/inactive and action is PBN), else don't update
            if new_user_restrict_ban.is_active and (
                not user_deactivated_inactive
                or (user_deactivated_inactive and violation_status == "PBN")
            ):
                # reported_user_query.update(
                #     {"status": action_duration[0]}, synchronize_session=False
                # )
                reported_user.status = violation_status

            db.commit()

        except SQLAlchemyError as exc:
            print(exc)
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing request",
            ) from exc

        message = f"Request processed successfully. Appropriate action taken. Report case number {action_request.case_number} resolved."

    # setting flag, to check if (no action or active action) or (action and future active)
    no_action_or_active_action = None
    if no_action or (not no_action and is_active):
        no_action_or_active_action = True
    elif not no_action and not is_active:
        no_action_or_active_action = False

    # common operations for both action and no action
    try:
        # if no action or active restrict/ban
        if no_action_or_active_action:
            # update report to resolved
            report_query.update(
                {"status": "RSD", "moderator_note": "RS"}, synchronize_session=False
            )

            # update scores
            user_guideline_violation_score_query.update(
                {
                    score_type: curr_score + effective_score,
                    "final_violation_score": new_final_violation_score,
                    # "last_added_score": effective_score,
                },
                synchronize_session=False,
            )

            # last added score entry
            user_guideline_violation_score.last_added_scores.append(
                admin_model.GuidelineViolationLastAddedScore(
                    last_added_score=effective_score,
                    score_id=user_guideline_violation_score.id,
                    report_id=report.id,
                )
            )

            # ban content
            content_to_be_deleted = post_query or comment_query  # type: ignore
            content_to_be_deleted.update(
                {"status": "BAN"},
                synchronize_session=False,
            )

        # if future action
        else:
            # update report status to future resolve
            report_query.update(
                {"status": "FRS", "moderator_note": "RS"}, synchronize_session=False
            )

            # we don't update the scores now, it will be updated when the action is active in future
            # last added score entry with is_active False
            user_guideline_violation_score.last_added_scores.append(
                admin_model.GuidelineViolationLastAddedScore(
                    last_added_score=effective_score,
                    score_id=user_guideline_violation_score.id,
                    report_id=report.id,
                    is_added=False,
                )
            )

            # flag content
            content_to_be_deleted = post_query or comment_query  # type: ignore
            content_to_be_deleted.update(
                {"status": "FLB"},
                synchronize_session=False,
            )

        # handled seperately
        # get related under review reports
        related_reports_query = (
            admin_service.get_related_reports_for_specific_report_query(
                case_number=action_request.case_number,
                reported_user_id=str(reported_user.id),
                reported_item_id=str(report.reported_item_id),
                reported_item_type=report.reported_item_type,
                status="URV",
                moderator_id=curr_employee.id,
                db_session=db,
            )
        )
        related_reports = related_reports_query.all()
        if related_reports:
            # check if other related reports have same report reason, if yes, resolve those, else close
            for related_report in related_reports:
                if related_report.report_reason == report.report_reason:
                    if no_action_or_active_action:
                        related_report.status = "RSR"
                        related_report.moderator_note = "RS"
                    else:
                        related_report.status = "FRR"
                        related_report.moderator_note = "RS"
                else:
                    related_report.status = "CSD"
                    related_report.moderator_note = "RF"

        db.commit()
    except SQLAlchemyError as exc:
        print(exc)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing request",
        ) from exc

    # send email if action status is TBN/PBN
    if new_user_restrict_ban and violation_status in ("TBN", "PBN"):
        # generate appeal link
        appeal_link = "https://vpkonnect.in/accounts/appeals/form_ban"
        email_subject = "VPKonnect - Account Ban"
        email_details = admin_schema.SendEmail(
            template=(
                "permanent_ban_email.html"
                if violation_status == "PBN"
                else "temporary_ban_email.html"
            ),
            email=[EmailStr(reported_user.email)],
            body_info={
                "username": reported_user.username,
                "link": appeal_link,
                "days": violation_duration // 24,
                "ban_enforced_datetime": new_user_restrict_ban.enforce_action_at.strftime(
                    "%b %d, %Y %H:%M %Z"
                ),
            },
        )

        try:
            email_utils.send_email(email_subject, email_details, background_tasks)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error sending email.",
            ) from exc

    moderator_note_full = map_utils.create_violation_moderator_notes(
        username=reported_user.username,
        moderator_note=report.moderator_note,
        case_number=action_request.case_number,
        content_type=report.reported_item_type,
        report_reason=report.report_reason,
    )

    if open_related_reports_put_under_review_message:
        return {
            "message": message,
            "detail": moderator_note_full,
            "additional_message": open_related_reports_put_under_review_message,
        }

    return {"message": message, "detail": moderator_note_full}


# use this mainly for account reports
# can also be used for other content types if need be
@router.post("/reports/action/manual")
def enforce_report_action_manual(
    action_request: admin_schema.EnforceReportActionManual,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email), db_session=db
    )

    # check identity
    if curr_employee and (action_request.moderator_emp_id != curr_employee.emp_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # get the report from case number
    report_query = admin_service.get_a_report_query(
        action_request.case_number, "URV", db
    )
    report = report_query.first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report to be taken action on, not found",
        )

    # check if the content exists or not
    if report.reported_item_type == "post":
        post_query = post_service.get_a_post_query(
            str(report.reported_item_id), ["DRF", "DEL"], db
        )
        post = post_query.first()
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Reported post not found"
            )
        if post.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported post already banned",
            )
        if post.status == "FLB":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported post already flagged to be banned",
            )

    elif report.reported_item_type == "comment":
        comment_query = comment_service.get_a_comment_query(
            str(report.reported_item_id), ["DEL"], db
        )
        comment = comment_query.first()
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported comment not found",
            )
        if comment.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported comment already banned",
            )
        if comment.status == "FLB":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported comment already flagged to be banned",
            )

    # for reported_item_type account reported_item_id and reported_user.id is same. So reported_user and account is same
    # for other content types, it is different
    reported_user_query = user_service.get_user_by_username_query(
        str(action_request.reported_username), ["PBN", "DEL"], db
    )
    reported_user = reported_user_query.first()
    if not reported_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user_deactivated_inactive = False
    if reported_user.status in [
        "DAH",
        "DAK",
        "PDH",
        "PDK",
        "INA",
    ]:
        user_deactivated_inactive = True
        # raise HTTPException(
        #     status_code=status.HTTP_404_NOT_FOUND,
        #     detail="User profile not found",
        # )

    # if there are any OPN related report(s) which were not noticed before, put it/them under review and consider it/them in this action request
    # get open related reports
    open_related_reports_to_be_reviewed = (
        admin_service.get_open_reports_for_specific_content_report(
            case_number=action_request.case_number,
            reported_item_id=report.reported_item_id,
            reported_item_type=report.reported_item_type,
            db_session=db,
        )
    )
    # get case numbers of the related reports if any
    open_related_reports_put_under_review_message = None
    if open_related_reports_to_be_reviewed:
        open_related_reports_case_numbers = [
            related_report.case_number
            for related_report in open_related_reports_to_be_reviewed
        ]
        if open_related_reports_case_numbers:
            selected_reports_under_review_update(
                reports_request=admin_schema.ReportUnderReviewUpdate(
                    case_number_list=open_related_reports_case_numbers
                ),
                db=db,
                current_employee=current_employee,
            )

            open_related_reports_put_under_review_message = f"Additional {len(open_related_reports_case_numbers)} related report(s), case number(s): {open_related_reports_case_numbers} was/were put under review and was/were included in this action request"

    # map action, duration with minimum required violation score
    min_req_violation_score = map_utils.action_entry_score_dict.get(
        (action_request.action, action_request.duration)
    )
    if not min_req_violation_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minimum required violation score not found",
        )

    # fetch the current final violation score
    user_guideline_violation_score_query = (
        admin_service.get_user_guideline_violation_score_query(
            str(reported_user.id), db
        )
    )
    user_guideline_violation_score = user_guideline_violation_score_query.first()
    if not user_guideline_violation_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User guideline violation score entry not found",
        )

    curr_final_violation_score = int(
        user_guideline_violation_score.final_violation_score
    )

    # set the score_type and get curr_score for the content type
    if report.reported_item_type == "post":
        score_type = "post_score"
        curr_score = user_guideline_violation_score.post_score
    elif report.reported_item_type == "comment":
        score_type = "comment_score"
        curr_score = user_guideline_violation_score.comment_score
    elif report.reported_item_type == "message":
        score_type = "message_score"
        curr_score = user_guideline_violation_score.message_score
    # if reported item type is account, then use post_score, as posts reflect most of the account
    else:
        score_type = "post_score"
        curr_score = user_guideline_violation_score.post_score

    # adjust the scores if action entry violation score is larger than current final violation score, difference is added to the content score
    if curr_final_violation_score < min_req_violation_score:
        new_final_violation_score = min_req_violation_score
        difference_score = min_req_violation_score - curr_final_violation_score
        new_content_score = curr_score + difference_score
        new_last_added_score = difference_score
    else:
        new_final_violation_score = curr_final_violation_score
        new_content_score = curr_score
        new_last_added_score = 0

    # update user_restrict_ban_detail, user_content_report_detail, user_content_report_event_timeline using trigger, guideline_violation_score and user tables
    # handle other under review reports if any, related to this content report, they need to be closed
    # ban/falg the content

    # get all restrict/ban entries for a user
    user_all_restrict_ban_query = admin_service.get_all_user_restrict_ban_query(
        reported_user.id, db
    )

    # check if there is any active restriction/ban
    user_active_restrict_ban = user_all_restrict_ban_query.filter(
        admin_model.UserRestrictBanDetail.is_active == True
    ).first()

    # check if there is/are any consecutive restrictions/bans already in line, in those get the latest one
    user_future_restrict_ban = (
        user_all_restrict_ban_query.filter(
            admin_model.UserRestrictBanDetail.enforce_action_at > func.now(),
            admin_model.UserRestrictBanDetail.is_active == False,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .order_by(admin_model.UserRestrictBanDetail.enforce_action_at.desc())
        .first()
    )

    is_active = None
    enforce_action_at = None
    # there is a active restrict/ban and also there is/are future restricts/bans in line
    if user_active_restrict_ban and user_future_restrict_ban:
        enforce_time = user_future_restrict_ban.enforce_action_at + timedelta(
            hours=user_future_restrict_ban.duration,
        )
        is_active = False
        enforce_action_at = enforce_time
    # there is a active restrict/ban and also there is/are no future restricts/bans in line
    elif user_active_restrict_ban and not user_future_restrict_ban:
        enforce_time = user_active_restrict_ban.enforce_action_at + timedelta(
            hours=user_active_restrict_ban.duration,
        )
        is_active = False
        enforce_action_at = enforce_time
    # no active restrict/ban
    elif not user_active_restrict_ban:
        is_active = True
        enforce_action_at = func.now()

    new_user_restrict_ban = admin_model.UserRestrictBanDetail(
        status=action_request.action,
        duration=action_request.duration,
        user_id=reported_user.id,
        is_active=is_active,
        content_type=report.reported_item_type,
        content_id=report.reported_item_id,
        report_id=report.id,
        enforce_action_at=enforce_action_at,
    )

    # add restrict/ban entry and update user status if needed
    try:
        # add restrict/ban entry
        db.add(new_user_restrict_ban)

        # update user status in user table only if action is enforced now i.e is_active = True and (user is not deactivated/inactive or user is deactivated/inactive and action is PBN, else don't update
        if (
            is_active
            and not user_deactivated_inactive
            or (user_deactivated_inactive and action_request.action == "PBN")
        ):
            # reported_user_query.update(
            #     {"status": action_duration[0]}, synchronize_session=False
            # )
            reported_user.status = action_request.action

        db.commit()
        # db.refresh(new_user_restrict_ban)
    except SQLAlchemyError as exc:
        print(exc)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing request",
        ) from exc

    try:
        # handled seperately
        # ban the contents flagged by manual/auto process, if reported_item_type is account
        if (
            report.reported_item_type == "account"
            and action_request.contents_to_be_banned
        ):
            flagged_posts_not_found = []
            for post_id in action_request.contents_to_be_banned:
                post_to_be_banned = post_service.get_a_post(
                    post_id=str(post_id),
                    status_not_in_list=["DRF", "DEL", "BAN", "FLB", "FLD"],
                    db_session=db,
                )
                # if flagged post not found then append it to the list and skip the rest of the operations, if found, then append to valid_flagged_posts
                if not post_to_be_banned:
                    flagged_posts_not_found.append(post_id)
                    continue
                else:
                    valid_flagged_content = admin_model.AccountReportFlaggedContent(
                        report_id=report.id, valid_flagged_content=post_id
                    )
                    db.add(valid_flagged_content)

                # ban the flagged post if active action
                # else, flag the post to be banned when action is enforced in future
                if is_active:
                    post_to_be_banned.status = "BAN"
                else:
                    post_to_be_banned.status = "FLB"

            number_of_posts_not_found = len(flagged_posts_not_found)
            number_of_flagged_posts_request = len(action_request.contents_to_be_banned)
            # if all the flagegd posts are not found then we need to raise the exception for moderator to look up account again
            if number_of_posts_not_found == number_of_flagged_posts_request:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="All posts flagged to be banned not found",
                )

            # adjust the violation scores as per the number of flagged posts
            # to make sure the violation scores are divisible by number of valid flagged posts
            number_of_valid_flagged_posts = (
                number_of_flagged_posts_request - number_of_posts_not_found
            )

            score_remainder_adjust = (
                new_final_violation_score % number_of_valid_flagged_posts
            )
            score_adjust = abs(number_of_valid_flagged_posts - score_remainder_adjust)
            new_final_violation_score = new_final_violation_score + score_adjust
            new_content_score = (
                new_content_score + score_adjust
                if new_content_score != curr_score
                else new_content_score
            )
            new_last_added_score = (
                new_last_added_score + score_adjust
                if new_last_added_score != 0
                else new_last_added_score
            )

        # if active action
        if is_active:
            report_query.update(
                {"status": "RSD", "moderator_note": "RS"}, synchronize_session=False
            )

            # update guideline violation score entry
            user_guideline_violation_score_query.update(
                {
                    score_type: new_content_score,
                    "final_violation_score": new_final_violation_score,
                    # "last_added_score": new_last_added_score,
                },
                synchronize_session=False,
            )

            # last added score entry
            user_guideline_violation_score.last_added_scores.append(
                admin_model.GuidelineViolationLastAddedScore(
                    last_added_score=new_last_added_score,
                    score_id=user_guideline_violation_score.id,
                    report_id=report.id,
                )
            )

            # ban content only if reported_item_type is post/comment
            # only if is_active is True, meaning action is enforced now
            if report.reported_item_type in ["post", "comment"]:
                content_to_be_banned = post_query or comment_query  # type: ignore
                # ban the content
                content_to_be_banned.update(
                    {"status": "BAN"},
                    synchronize_session=False,
                )

        # if future action
        else:
            # update report status to future resolve
            report_query.update(
                {"status": "FRS", "moderator_note": "RS"}, synchronize_session=False
            )

            # last added score entry with is_active False
            user_guideline_violation_score.last_added_scores.append(
                admin_model.GuidelineViolationLastAddedScore(
                    last_added_score=new_last_added_score,
                    score_id=user_guideline_violation_score.id,
                    report_id=report.id,
                    is_added=False,
                )
            )

            # flag content
            # flag content only if reported_item_type is post/comment
            if report.reported_item_type in ["post", "comment"]:
                content_to_be_flagged_ban = post_query or comment_query  # type: ignore
                content_to_be_flagged_ban.update(
                    {"status": "FLB"},
                    synchronize_session=False,
                )

        # get related under review reports
        related_reports_query = (
            admin_service.get_related_reports_for_specific_report_query(
                case_number=action_request.case_number,
                reported_user_id=str(reported_user.id),
                reported_item_id=str(report.reported_item_id),
                reported_item_type=report.reported_item_type,
                status="URV",
                moderator_id=curr_employee.id,
                db_session=db,
            )
        )

        # handled seperately
        related_reports = related_reports_query.all()
        if related_reports:
            # check if other related reports have same report reason, if yes, resolve those, else close
            for related_report in related_reports:
                if related_report.report_reason == report.report_reason:
                    if is_active:
                        related_report.status = "RSR"
                        related_report.moderator_note = "RS"
                    else:
                        related_report.status = "FRR"
                        related_report.moderator_note = "RS"
                else:
                    related_report.status = "CSD"
                    related_report.moderator_note = "RF"

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing request",
        ) from exc
    except HTTPException as exc:
        db.rollback()
        raise exc

    # send email if action status is TBN/PBN
    if new_user_restrict_ban and action_request.action in ("TBN", "PBN"):
        # generate appeal link
        appeal_link = "https://vpkonnect.in/accounts/appeals/form_ban"

        email_subject = "VPKonnect - Account Ban"
        email_details = admin_schema.SendEmail(
            template=(
                "permanent_ban_email.html"
                if action_request.action == "PBN"
                else "temporary_ban_email.html"
            ),
            email=[EmailStr(reported_user.email)],
            body_info={
                "username": reported_user.username,
                "link": appeal_link,
                "days": action_request.duration // 24,
                "ban_enforced_datetime": new_user_restrict_ban.enforce_action_at.strftime(
                    "%b %d, %Y %H:%M %Z"
                ),
            },
        )

        try:
            email_utils.send_email(email_subject, email_details, background_tasks)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error sending email.",
            ) from exc

    moderator_note_full = map_utils.create_violation_moderator_notes(
        username=reported_user.username,
        moderator_note=report.moderator_note,
        case_number=action_request.case_number,
        content_type=report.reported_item_type,
        report_reason=report.report_reason,
    )

    message = f"Request processed successfully. Requested action taken. Report case number {action_request.case_number} resolved."
    if open_related_reports_put_under_review_message:
        return {
            "message": message,
            "detail": moderator_note_full,
            "additional_message": open_related_reports_put_under_review_message,
        }

    return {
        "message": message,
        "detail": moderator_note_full,
    }


@router.patch("/reports/{case_number}/close")
def close_report(
    case_number: int,
    close_request: admin_schema.CloseReport,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email), db_session=db
    )

    # check identity
    if curr_employee and (close_request.moderator_emp_id != curr_employee.emp_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    # get the report from case number
    report_query = admin_service.get_a_report_query(case_number, "URV", db)
    report = report_query.first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report to be taken action on, not found",
        )

    # update the report
    report_query.update(
        {"status": "CSD", "moderator_note": close_request.moderator_note},
        synchronize_session=False,
    )

    # get other related reports with same report reason, if any then update the status and moderator_note of the related reports same as the report
    related_reports_query = admin_service.get_related_reports_for_specific_report_query(
        case_number=case_number,
        reported_user_id=str(report.reported_user_id),
        reported_item_id=str(report.reported_item_id),
        reported_item_type=report.reported_item_type,
        status="URV",
        moderator_id=curr_employee.id,
        db_session=db,
    )
    related_reports_same_reason_query = related_reports_query.filter(
        admin_model.UserContentReportDetail.report_reason == report.report_reason
    )
    related_reports_same_reason = related_reports_same_reason_query.all()

    if related_reports_same_reason:
        for related_report in related_reports_same_reason:
            related_report.status = "CSD"
            related_report.moderator_note = close_request.moderator_note

    db.commit()

    moderator_note_full = map_utils.create_violation_moderator_notes(
        username=close_request.reported_username,
        moderator_note=close_request.moderator_note,
        case_number=case_number,
        content_type=report.reported_item_type,
        report_reason=report.report_reason,
    )

    return {
        "message": f"Request processed successfully. No action taken. Report case number {case_number} closed.",
        "detail": moderator_note_full,
    }


# dummy endpoint for appeal accept
@router.patch("/appeals/action")
def appeal_action(
    request: admin_schema.AppealAction,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.AccessRoleDependency(role="content_mgmt")
    ),
):
    if request.action == "accept":
        # get and accept the appeal
        appeal_entry = (
            db.query(admin_model.UserContentRestrictBanAppealDetail)
            .filter(
                admin_model.UserContentRestrictBanAppealDetail.case_number
                == request.case_number,
                admin_model.UserContentRestrictBanAppealDetail.user_id
                == request.user_id,
                admin_model.UserContentRestrictBanAppealDetail.report_id
                == request.report_id,
                admin_model.UserContentRestrictBanAppealDetail.content_type
                == request.content_type,
                admin_model.UserContentRestrictBanAppealDetail.content_id
                == request.content_id,
                admin_model.UserContentRestrictBanAppealDetail.status == "URV",
                admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
            )
            .first()
        )

        if appeal_entry:
            appeal_entry.status = "ACP"
        else:
            print("Error")
            return None
    else:
        appeal_entry = (
            db.query(admin_model.UserContentRestrictBanAppealDetail)
            .filter(
                admin_model.UserContentRestrictBanAppealDetail.case_number
                == request.case_number,
                admin_model.UserContentRestrictBanAppealDetail.user_id
                == request.user_id,
                admin_model.UserContentRestrictBanAppealDetail.report_id
                == request.report_id,
                admin_model.UserContentRestrictBanAppealDetail.content_type
                == request.content_type,
                admin_model.UserContentRestrictBanAppealDetail.content_id
                == request.content_id,
                admin_model.UserContentRestrictBanAppealDetail.status == "OPN",
                admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
            )
            .first()
        )

        if appeal_entry:
            appeal_entry.status = "URV"
            appeal_entry.moderator_id = request.moderator_id
        else:
            print("Error")
            return None

    db.commit()

    return {"message": f"Appeal case number:{request.case_number} accepted."}
