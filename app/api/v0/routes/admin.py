from datetime import date, timedelta
from math import floor
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query
from fastapi import status as http_status
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import admin as admin_model
from app.schemas import admin as admin_schema
from app.schemas import auth as auth_schema
from app.schemas import employee as employee_schema
from app.schemas import post as post_schema
from app.schemas import user as user_schema
from app.services import admin as admin_service
from app.services import comment as comment_service
from app.services import employee as employee_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import email as email_utils
from app.utils import map as map_utils
from app.utils import operation as operation_utils
from app.utils.exception import CustomValidationError

router = APIRouter(prefix=settings.api_prefix + "/admin", tags=["Admin"])


# reports dashboard
@router.get(
    "/reports/dashboard",
    response_model=list[admin_schema.AllReportResponse],
)
@auth_utils.authorize(["content_admin", "content_mgmt"])
def get_reports_dashboard(
    status: (
        Literal[
            "open",
            "closed",
            "review",
            "resolved",
            "future_resolved",
        ]
        | None
    ) = Query(None),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # transform report status
    try:
        report_status = map_utils.transform_status(value=status) if status else ["OPN"]
    except HTTPException as exc:
        raise exc

    # get curr employee
    curr_moderator_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get reports based on status and moderator
    all_reports = admin_service.get_all_reports_by_status_moderator_id_reported_at(
        status_in_list=report_status,
        moderator_id=curr_moderator_employee.id,
        reported_at=None,
        db_session=db,
    )

    if not all_reports:
        return []

    all_reports_response = [
        admin_schema.AllReportResponse(
            case_number=report.case_number,
            status=report.status,
            reported_at=report.created_at,
        )
        for report in all_reports
    ]

    return all_reports_response


@router.get(
    "/reports/admin-dashboard", response_model=list[admin_schema.AllReportResponse]
)
@auth_utils.authorize(["content_admin"])
def get_reports_admin_dashboard(
    type_: Literal["new", "assigned"] = Query(),
    status: (
        Literal[
            "open",
            "closed",
            "review",
            "resolved",
            "future_resolved",
        ]
        | None
    ) = Query(None),
    emp_id: str = Query(None),
    reported_at: date = Query(None, description="date format YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # check parameters
    if status != "open" and type_ == "new":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {type_} for status: {status}",
        )
    if type_ == "new" and emp_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {emp_id} for type: {type_}",
        )

    # transform report status
    try:
        report_status = map_utils.transform_status(value=status) if status else ["OPN"]
    except HTTPException as exc:
        raise exc

    moderator = None
    if emp_id:
        moderator = employee_service.get_employee_by_emp_id(
            emp_id=emp_id,
            status_not_in_list=["SUP", "TER"],
            db_session=db,
        )

    # fetch all reports
    all_reports = admin_service.get_all_reports_by_status_moderator_id_reported_at(
        status_in_list=report_status,
        db_session=db,
        moderator_id=moderator.id if moderator else None,
        reported_at=reported_at,
        type_=type_,
    )

    if not all_reports:
        return []

    # prepare the response
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
@auth_utils.authorize(["content_admin", "content_mgmt"])
def get_requested_report(
    case_number: int,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get the report
    requested_report = admin_service.get_a_report(
        case_number=case_number, status_in_list=None, db_session=db
    )
    if not requested_report:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Report not found"
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
                status_code=http_status.HTTP_404_NOT_FOUND,
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
        "case_number": requested_report.case_number,
        "reporter_user": requested_report.reporter_user.__dict__,
        "reported_user": requested_report.reported_user.__dict__,
        "reported_item_type": requested_report.reported_item_type,
        "reported_item": (
            (requested_report.post.__dict__ if requested_report.post else None)
            or (requested_report.comment.__dict__ if requested_report.comment else None)
            or requested_report.account.__dict__
        ),
        "flagged_banned_posts": flagged_banned_posts_ids,
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
        "account_restrict_ban": (
            requested_report.restrict_ban.__dict__
            if requested_report.restrict_ban
            else None
        ),
        "effective_user_status": requested_report.reported_user.__dict__.get("status"),
        "moderator": (
            requested_report.moderator.__dict__ if requested_report.moderator else None
        ),
        "reported_at": requested_report.created_at,
        "last_updated_at": requested_report.updated_at,
    }

    return admin_schema.ReportResponse.parse_obj(requested_report_data)


# get all other open reports related to a particular content report
@router.get(
    "/reports/{case_number}/related",
    response_model=list[admin_schema.AllReportResponse],
)
@auth_utils.authorize(["content_admin", "content_mgmt"])
def get_all_related_open_reports_for_specific_report(
    case_number: int,
    admin: bool = Query(),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    if admin:
        specific_report = admin_service.get_a_report(
            case_number=case_number,
            status_in_list=["OPN"],
            db_session=db,
        )
        if not specific_report:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Specific report not found",
            )
        if specific_report.moderator_id:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="This specific report is already assigned",
            )
        moderator_id = None

    else:
        moderator_id = curr_employee.id
        # get the report using case_number (OPN or URV, sometimes we may need to check OPN reports for a URV report too)
        specific_report = admin_service.get_a_report(
            case_number=case_number,
            status_in_list=["OPN", "URV"],
            db_session=db,
        )
        if not specific_report:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Specific report not found",
            )
        if not specific_report.moderator_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform requested action. Report is not assigned by admin",
            )

    # get other reports
    all_other_reports = admin_service.get_open_reports_for_specific_content_report(
        case_number=specific_report.case_number,
        reported_item_id=specific_report.reported_item_id,
        reported_item_type=specific_report.reported_item_type,
        report_reason=None,
        report_reason_user=specific_report.report_reason_user_id,
        db_session=db,
        moderator_id=moderator_id,
    )

    if not all_other_reports:
        return []

    # loop through the list of UserContentReportDetail objects and get required params
    # create response object
    all_other_reports_response = [
        admin_schema.AllReportResponse(
            case_number=report.case_number,
            status=report.status,
            reported_at=report.created_at,
        )
        for report in all_other_reports
    ]

    return all_other_reports_response


# select reports to review
@router.patch("/reports/review")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def selected_reports_under_review_update(
    reports_request: admin_schema.ReportUnderReviewUpdate,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
    is_func_call: bool = False,
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # check if each report to be marked for review exists or not, are they open are not
    # update the valid reports
    valid_reports = []
    invalid_reports = []
    already_urv_reports = []
    messages = []
    errors = []

    for case_no in reports_request.case_number_list:
        get_report_query = admin_service.get_a_report_query(
            case_number=case_no, status_in_list=["OPN", "URV"], db_session=db
        )
        get_report = get_report_query.first()
        if not get_report or get_report.moderator_id != curr_employee.id:
            invalid_reports.append(case_no)
        elif get_report.status == "URV":
            already_urv_reports.append(case_no)
        else:
            get_report_query.update(
                {"status": "URV"},
                synchronize_session=False,
            )
            valid_reports.append(case_no)

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing select reports review/assign request",
        ) from exc

    if is_func_call:
        return valid_reports

    # if not func call
    if valid_reports:
        messages.append(
            f"{len(valid_reports)} report(s), case number(s): {valid_reports} is/are marked for review"
        )
    else:
        messages.append("No valid reports to mark for review")

    if invalid_reports:
        errors.append(
            f"{len(invalid_reports)} report(s), case number(s): {invalid_reports} could not be marked for review due to internal error. These report(s) might already be closed/resolved by concerned moderators"
        )

    if already_urv_reports:
        errors.append(
            f"{len(already_urv_reports)} report(s), case number(s): {already_urv_reports} is/are already under review"
        )

    return {
        "message": " ".join(messages),
        "error": "\n".join(errors) if errors else None,
    }


@router.patch("/reports/assign")
@auth_utils.authorize(["content_admin"])
def selected_reports_assign_update(
    reports_request: admin_schema.ReportAssignUpdate,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the moderator to be assigned
    moderator = employee_service.get_employee_by_emp_id(
        emp_id=reports_request.moderator_emp_id,
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )
    if not moderator:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Moderator to be assigned to a report not found",
        )

    # check if each report to be assigned exists or not, are they open are not
    # update the valid reports
    valid_reports = []
    invalid_reports = []
    already_assigned_reports = []
    messages = []
    errors = []

    for case_no in reports_request.case_number_list:
        get_report_query = admin_service.get_a_report_query(
            case_number=case_no, status_in_list=["OPN"], db_session=db
        )
        get_report = get_report_query.first()
        if not get_report:
            invalid_reports.append(case_no)
        elif get_report.moderator_id:
            already_assigned_reports.append(case_no)
        else:
            get_report_query.update(
                {"moderator_id": moderator.id},
                synchronize_session=False,
            )
            valid_reports.append(case_no)

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing select reports assign request",
        ) from exc

    # if not func call
    if valid_reports:
        messages.append(
            f"{len(valid_reports)} report(s), case number(s): {valid_reports} is/are assigned to {moderator.id}"
        )
    else:
        messages.append(f"No valid reports to assign to {moderator.id}")

    if invalid_reports:
        errors.append(
            f"{len(invalid_reports)} report(s), case number(s): {invalid_reports} could not be assigned to {moderator.id} due to internal error. These report(s) might already be closed/resolved by concerned moderators"
        )

    if already_assigned_reports:
        errors.append(
            f"{len(already_assigned_reports)} report(s), case number(s): {already_assigned_reports} is/are already assigned to a moderator"
        )

    return {
        "message": " ".join(messages),
        "error": "\n".join(errors) if errors else None,
    }


@router.patch("/reports/{case_number}/close")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def close_report(
    case_number: int,
    close_request: admin_schema.CloseReport,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the report from case number
    report_query = admin_service.get_a_report_query(
        case_number=case_number, status_in_list=["CSD", "URV"], db_session=db
    )
    report = report_query.first()
    if not report:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Report to be taken action on, not found",
        )

    if report.moderator_id != curr_employee.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    if report.status == "CSD":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT, detail="Report is already closed"
        )

    # if there are any OPN related report(s) which were not noticed before, put it/them under review and consider it/them in this action request
    # get open related reports
    open_related_reports_to_be_reviewed = (
        admin_service.get_open_reports_for_specific_content_report(
            case_number=case_number,
            reported_item_id=report.reported_item_id,
            reported_item_type=report.reported_item_type,
            report_reason=report.report_reason,
            report_reason_user=report.report_reason_user_id,
            db_session=db,
            moderator_id=report.moderator_id,
        )
    )
    open_related_reports_put_under_review_message = None

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

    try:
        # update the report
        report_query.update(
            {"status": "CSD", "moderator_note": close_request.moderator_note},
            synchronize_session=False,
        )

        # open related reports if any
        if open_related_reports_to_be_reviewed:
            open_related_reports_case_numbers = [
                related_report.case_number
                for related_report in open_related_reports_to_be_reviewed
            ]
            if open_related_reports_case_numbers:
                valid_reports = selected_reports_under_review_update(
                    reports_request=admin_schema.ReportUnderReviewUpdate(
                        case_number_list=open_related_reports_case_numbers
                    ),
                    db=db,
                    current_employee=current_employee,
                    is_func_call=True,
                )

                open_related_reports_put_under_review_message = f"Additional {len(valid_reports)} related report(s), case number(s): {valid_reports} was/were put under review and was/were processed in this close request"

        # related reports
        if related_reports_same_reason:
            for related_report in related_reports_same_reason:
                related_report.status = "CSD"
                related_report.moderator_note = close_request.moderator_note

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing close report request",
        ) from exc

    moderator_note_full = map_utils.create_violation_moderator_notes(
        username=report.reported_user.username,
        moderator_note=close_request.moderator_note,
        case_number=case_number,
        content_type=report.reported_item_type,
        report_reason=report.report_reason,
    )

    message = f"Request processed successfully. No action taken. Report case number {case_number} closed."
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


# violation enforcement action algorithm, we use this only for post, comment and message reports
# for account reports, use manual action
@router.post("/reports/action/auto")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def enforce_report_action_auto(
    action_request: admin_schema.EnforceReportActionAuto,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the report from case number
    report_query = admin_service.get_a_report_query(
        case_number=action_request.case_number,
        status_in_list=["OPN", "FRS", "FRR", "RSD", "RSR", "URV", "CSD"],
        db_session=db,
    )
    report = report_query.first()
    if not report:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Report to be taken action on, not found",
        )
    if report.moderator_id != curr_employee.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )
    if report.status == "OPN":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Report should be under review for action to be taken",
        )
    elif report.status == "CSD":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Report to be taken action on, is closed",
        )
    elif report.status in ("FRR", "FRS", "RSD", "RSR"):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Action has been already taken on this report",
        )

    # check if the content exists or not
    if report.reported_item_type == "account":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Requested action cannot be performed. Please use Manual Action",
        )

    elif report.reported_item_type == "post":
        post_query = post_service.get_a_post_query(
            post_id=str(report.reported_item_id),
            status_not_in_list=["DRF", "RMV", "FLD"],
            db_session=db,
        )
        post = post_query.first()
        if not post:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported post not found",
            )
        if post.status == "BAN":
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported post already banned",
            )
        if post.status == "FLB":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported post already flagged to be banned",
            )

    elif report.reported_item_type == "comment":
        comment_query = comment_service.get_a_comment_query(
            comment_id=str(report.reported_item_id),
            status_not_in_list=["FLD", "RMV"],
            db_session=db,
        )
        comment = comment_query.first()
        if not comment:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported comment not found",
            )
        if comment.status == "BAN":
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported comment already banned",
            )
        if comment.status == "FLB":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported comment already flagged to be banned",
            )

    # get reported user
    reported_user_query = user_service.get_user_by_username_query(
        username=str(action_request.reported_username),
        status_not_in_list=["PDI", "PDB", "DEL"],
        db_session=db,
    )
    reported_user = reported_user_query.first()
    if not reported_user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if reported_user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Reported user is permanently banned",
        )

    user_deactivated_inactive = False
    if reported_user.status in ("DAH", "PDH", "INA"):
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
            report_reason=None,
            report_reason_user=report.report_reason_user_id,
            db_session=db,
            moderator_id=report.moderator_id,
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
            valid_reports = selected_reports_under_review_update(
                reports_request=admin_schema.ReportUnderReviewUpdate(
                    case_number_list=open_related_reports_case_numbers
                ),
                db=db,
                current_employee=current_employee,
                is_func_call=True,
            )

            open_related_reports_put_under_review_message = f"Additional {len(valid_reports)} related report(s), case number(s): {valid_reports} was/were put under review and was/were included in this action request"

    # map report reason to severity group
    severity_group = map_utils.report_reasons_severity_group_dict.get(
        report.report_reason
    )
    if not severity_group:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Severity group not found",
        )

    if severity_group == "CMD":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Requested action cannot be performed. Please use Manual Action",
        )

    # map severity group to severity score
    severity_score = map_utils.severity_groups_scores_dict.get(severity_group)
    if not severity_score:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Severity score not found",
        )

    # map content type to weights
    content_weight = map_utils.content_weigths_dict.get(report.reported_item_type)
    if not content_weight:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Content weight not found",
        )

    # fetch the current final violation score
    user_guideline_violation_score_query = (
        admin_service.get_user_guideline_violation_score_query(
            user_id=str(reported_user.id), db_session=db
        )
    )
    user_guideline_violation_score = user_guideline_violation_score_query.first()
    if not user_guideline_violation_score:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
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
                status_code=http_status.HTTP_404_NOT_FOUND, detail="No action found"
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
            user_id=reported_user.id, db_session=db
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

        message = f"Request processed successfully. Appropriate action taken. Report case number {action_request.case_number} resolved."

    # setting flag, to check if (no action or active action) or (action and future active)
    no_action_or_active_action = None
    if no_action or (not no_action and is_active):
        no_action_or_active_action = True
    elif not no_action and not is_active:
        no_action_or_active_action = False

    # common operations for both action and no action
    # add restrict ban entry and user status update if action
    # send mail
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

        # user status to be updated at the end if any action
        if not no_action and new_user_restrict_ban:
            # add restrict/ban entry
            db.add(new_user_restrict_ban)

            # update user status in user table only if action is enforced now i.e is_active = True and (user is not deactivated/inactive or (user is deactivated/inactive and action is PBN and status is not PDH), else don't update
            if new_user_restrict_ban.is_active and (
                not user_deactivated_inactive
                or (violation_status == "PBN" and reported_user.status != "PDH")
            ):
                # reported_user_query.update(
                #     {"status": action_duration[0]}, synchronize_session=False
                # )
                reported_user.status = violation_status

            # send email if action status is TBN/PBN and active action
            if is_active and violation_status in ("TBN", "PBN"):
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

                email_utils.send_email(email_subject, email_details, background_tasks)

        db.commit()
    except SQLAlchemyError as exc:
        print(exc)
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing enforce action request",
        ) from exc
    except Exception as exc:
        print(exc)
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
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

    return {
        "message": message,
        "detail": moderator_note_full,
    }


# use this mainly for account reports
# can also be used for other content types if need be
@router.post("/reports/action/manual")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def enforce_report_action_manual(
    action_request: admin_schema.EnforceReportActionManual,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the report from case number
    report_query = admin_service.get_a_report_query(
        case_number=action_request.case_number,
        status_in_list=["FRS", "FRR", "RSD", "RSR", "URV", "CSD"],
        db_session=db,
    )
    report = report_query.first()
    if not report:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Report to be taken action on, not found",
        )
    if report.moderator_id != curr_employee.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )
    if report.status == "CSD":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Report to be taken action on, is closed",
        )
    elif report.status in ("FRR", "FRS", "RSD", "RSR"):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Action has been already taken on this report",
        )

    # check if the content exists or not
    if report.reported_item_type == "post":
        post_query = post_service.get_a_post_query(
            post_id=str(report.reported_item_id),
            status_not_in_list=["DRF", "FLD", "RMV"],
            db_session=db,
        )
        post = post_query.first()
        if not post:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported post not found",
            )
        if post.status == "BAN":
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported post already banned",
            )
        if post.status == "FLB":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported post already flagged to be banned",
            )

    elif report.reported_item_type == "comment":
        comment_query = comment_service.get_a_comment_query(
            comment_id=str(report.reported_item_id),
            status_not_in_list=["FLD", "RMV"],
            db_session=db,
        )
        comment = comment_query.first()
        if not comment:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported comment not found",
            )
        if comment.status == "BAN":
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Reported comment already banned",
            )
        if comment.status == "FLB":
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Reported comment already flagged to be banned",
            )

    # for reported_item_type account reported_item_id and reported_user.id is same. So reported_user and account is same
    # for other content types, it is different
    reported_user_query = user_service.get_user_by_username_query(
        username=str(action_request.reported_username),
        status_not_in_list=["PDI", "PDB", "DEL"],
        db_session=db,
    )
    reported_user = reported_user_query.first()
    if not reported_user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if reported_user.status == "PBN":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Reported user is permanently banned",
        )

    user_deactivated_inactive = False
    if reported_user.status in ("DAH", "PDH", "INA"):
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
            report_reason=None,
            report_reason_user=report.report_reason_user_id,
            db_session=db,
            moderator_id=report.moderator_id,
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
            valid_reports = selected_reports_under_review_update(
                reports_request=admin_schema.ReportUnderReviewUpdate(
                    case_number_list=open_related_reports_case_numbers
                ),
                db=db,
                current_employee=current_employee,
                is_func_call=True,
            )

            open_related_reports_put_under_review_message = f"Additional {len(valid_reports)} related report(s), case number(s): {valid_reports} was/were put under review and was/were included in this action request"

    # map action, duration with minimum required violation score
    min_req_violation_score = map_utils.action_entry_score_dict.get(
        (action_request.action, action_request.duration)
    )
    if not min_req_violation_score:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Minimum required violation score not found",
        )

    # fetch the current final violation score
    user_guideline_violation_score_query = (
        admin_service.get_user_guideline_violation_score_query(
            user_id=str(reported_user.id), db_session=db
        )
    )
    user_guideline_violation_score = user_guideline_violation_score_query.first()
    if not user_guideline_violation_score:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
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
        user_id=reported_user.id, db_session=db
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
                    status_not_in_list=["DRF", "RMV", "BAN", "FLB", "FLD"],
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
                    status_code=http_status.HTTP_404_NOT_FOUND,
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

        # add restrict/ban entry and update user status if needed
        # user status is updated at the end
        db.add(new_user_restrict_ban)

        # update user status in user table only if action is enforced now i.e is_active = True and (user is not deactivated/inactive or (user is deactivated/inactive and action is PBN and status is not PDH), else don't update
        if (
            is_active
            and not user_deactivated_inactive
            or (
                user_deactivated_inactive
                and action_request.action == "PBN"
                and reported_user.status != "PDH"
            )
        ):
            # reported_user_query.update(
            #     {"status": action_duration[0]}, synchronize_session=False
            # )
            reported_user.status = action_request.action

        # send email if action status is TBN/PBN and active action
        if is_active and action_request.action in ("TBN", "PBN"):
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

            email_utils.send_email(email_subject, email_details, background_tasks)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing enforce action request",
        ) from exc
    except Exception as exc:
        print(exc)
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
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


# reports admin dashboard
@router.get(
    "/appeals/admin-dashboard", response_model=list[admin_schema.AllAppealResponse]
)
@auth_utils.authorize(["content_admin"])
def get_appeals_admin_dashboard(
    type_: Literal["new", "assigned"] = Query(),
    status: (
        Literal[
            "open",
            "closed",
            "review",
            "accepted",
            "rejected",
        ]
        | None
    ) = Query(None),
    emp_id: str = Query(None),
    reported_at: date = Query(None, description="date format YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # check parameters
    if status != "open" and type_ == "new":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {type_} for status: {status}",
        )
    if type_ == "new" and emp_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {emp_id} for type: {type_}",
        )

    # transform report status
    try:
        appeal_status = map_utils.transform_status(value=status) if status else ["OPN"]
    except HTTPException as exc:
        raise exc

    moderator = None
    if emp_id:
        moderator = employee_service.get_employee_by_emp_id(
            emp_id=emp_id,
            status_not_in_list=["SUP", "TER"],
            db_session=db,
        )

    # fetch all appeals
    all_appeals = admin_service.get_all_appeals_by_status_moderator_id_reported_at(
        status_in_list=appeal_status,
        db_session=db,
        moderator_id=moderator.id if moderator else None,
        reported_at=reported_at,
        type_=type_,
    )

    if not all_appeals:
        return []

    # prepare the response
    all_appeals_response = [
        admin_schema.AllAppealResponse(
            case_number=appeal.case_number,
            status=appeal.status,
            appealed_at=appeal.created_at,
        )
        for appeal in all_appeals
    ]

    return all_appeals_response


@router.get(
    "/appeals/dashboard",
    response_model=list[admin_schema.AllAppealResponse],
)
@auth_utils.authorize(["content_admin", "content_mgmt"])
def get_appeals_dashboard(
    status: (
        Literal[
            "open",
            "closed",
            "review",
            "accepted",
            "rejected",
        ]
        | None
    ) = Query(None),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # transform report status
    try:
        appeal_status = map_utils.transform_status(value=status) if status else ["OPN"]
    except HTTPException as exc:
        raise exc

    # get curr employee
    curr_moderator_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get appeals based on status and moderator
    all_appeals = admin_service.get_all_appeals_by_status_moderator_id_reported_at(
        status_in_list=appeal_status,
        moderator_id=curr_moderator_employee.id,
        reported_at=None,
        db_session=db,
    )

    if not all_appeals:
        return []

    all_appeals_response = [
        admin_schema.AllAppealResponse(
            case_number=report.case_number,
            status=report.status,
            appealed_at=report.created_at,
        )
        for report in all_appeals
    ]

    return all_appeals_response


@router.get("/appeals/{case_number}")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def get_requested_appeal(
    case_number: int,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get the appeal
    requested_appeal = admin_service.get_an_appeal(
        case_number=case_number, status_in_list=None, db_session=db
    )
    if not requested_appeal:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Appeal not found"
        )

    # we create the dict and then parse it using overriding parse_obj function on AppealResponse schema
    requested_appeal_data = {
        "case_number": requested_appeal.case_number,
        "appeal_user": requested_appeal.appeal_user.__dict__,
        "report": requested_appeal.report.__dict__,
        "content_type": requested_appeal.content_type,
        "appealed_content": (
            (requested_appeal.post.__dict__ if requested_appeal.post else None)
            or (requested_appeal.comment.__dict__ if requested_appeal.comment else None)
            or requested_appeal.account.__dict__
        ),
        "appeal_detail": requested_appeal.appeal_detail,
        "attachment": requested_appeal.attachment,
        "status": requested_appeal.status,
        "moderator_note": requested_appeal.moderator_note,
        "moderator": (
            requested_appeal.moderator.__dict__ if requested_appeal.moderator else None
        ),
        "appealed_at": requested_appeal.created_at,
        "last_updated_at": requested_appeal.updated_at,
    }

    return admin_schema.AppealResponse.parse_obj(requested_appeal_data)


@router.get(
    "/appeals/{case_number}/related",
    response_model=list[admin_schema.AllAppealResponse],
)
@auth_utils.authorize(["content_admin", "content_mgmt"])
def get_all_related_open_appeals_for_specific_appeal(
    case_number: int,
    admin: bool = Query(),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    if admin:
        specific_appeal = admin_service.get_an_appeal(case_number, ["OPN"], db)
        if not specific_appeal:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Specific appeal not found",
            )
        if specific_appeal.moderator_id:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="This specific appeal is already assigned",
            )
        moderator_id = None

    else:
        moderator_id = curr_employee.id
        # get the appeal using case_number (OPN or URV, sometimes we may need to check OPN appeals for a URV appeal too)
        specific_appeal = admin_service.get_an_appeal(case_number, ["OPN", "URV"], db)
        if not specific_appeal:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Specific appeal not found",
            )
        if not specific_appeal.moderator_id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Not authorized to perform requested action. Appeal is not assigned by admin",
            )

    # get other appeals
    all_other_appeals = admin_service.get_open_appeals_for_specific_content_appeal(
        case_number=specific_appeal.case_number,
        content_id=specific_appeal.content_id,
        content_type=specific_appeal.content_type,
        db_session=db,
        moderator_id=moderator_id,
    )

    if not all_other_appeals:
        return []

    all_other_appeals_response = [
        admin_schema.AllAppealResponse(
            case_number=appeal.case_number,
            status=appeal.status,
            appealed_at=appeal.created_at,
        )
        for appeal in all_other_appeals
    ]

    return all_other_appeals_response


# select appeals to review
@router.patch("/appeals/review")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def selected_appeals_under_review_update(
    appeals_request: admin_schema.AppealUnderReviewUpdate,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
    is_func_call: bool = False,
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # check if each appeal to be marked for review exists or not, are they open are not
    # update the valid appeals
    valid_appeals = []
    invalid_appeals = []
    already_urv_appeals = []
    messages = []
    errors = []
    for case_no in appeals_request.case_number_list:
        get_appeal_query = admin_service.get_an_appeal_query(
            case_no, ["OPN", "URV"], db
        )
        get_appeal = get_appeal_query.first()
        if (
            not get_appeal
            or not get_appeal.moderator_id
            or get_appeal.moderator_id != curr_employee.id
        ):
            invalid_appeals.append(case_no)
        elif get_appeal.status == "URV":
            already_urv_appeals.append(case_no)
        else:
            get_appeal_query.update(
                {"status": "URV"},
                synchronize_session=False,
            )
            valid_appeals.append(case_no)

    db.commit()

    if is_func_call:
        return valid_appeals

    # if not func call
    if valid_appeals:
        messages.append(
            f"{len(valid_appeals)} appeal(s), case number(s): {valid_appeals} is/are marked for review"
        )
    else:
        messages.append("No valid appeals to mark for review")

    if invalid_appeals:
        errors.append(
            f"{len(invalid_appeals)} appeal(s), case number(s): {invalid_appeals} could not be marked for review due to internal error. These appeal(s) might already be closed/resolved by concerned moderators"
        )

    if already_urv_appeals:
        errors.append(
            f"{len(already_urv_appeals)} appeal(s), case number(s): {already_urv_appeals} is/are already under review"
        )

    return {
        "message": " ".join(messages),
        "error": "\n".join(errors) if errors else None,
    }


# select appeals to assign
@router.patch("/appeals/assign")
@auth_utils.authorize(["content_admin"])
def selected_appeals_assign_update(
    appeals_request: admin_schema.AppealAssignUpdate,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the moderator to be assigned
    moderator = employee_service.get_employee_by_emp_id(
        emp_id=appeals_request.moderator_emp_id,
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )
    if not moderator:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Moderator to be assigned to an appeal not found",
        )

    # check if each appeal to be assigned exists or not, are they open are not
    # update the valid appeals
    valid_appeals = []
    invalid_appeals = []
    already_assign_appeals = []
    messages = []
    errors = []
    for case_no in appeals_request.case_number_list:
        get_appeal_query = admin_service.get_an_appeal_query(
            case_number=case_no, status_in_list=["OPN"], db_session=db
        )
        get_appeal = get_appeal_query.first()
        if not get_appeal:
            invalid_appeals.append(case_no)
        elif get_appeal.moderator_id:
            already_assign_appeals.append(case_no)
        else:
            get_appeal_query.update(
                {"moderator_id": moderator.id},
                synchronize_session=False,
            )
            valid_appeals.append(case_no)

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing select appeals assign request",
        ) from exc

    # if not func call
    if valid_appeals:
        messages.append(
            f"{len(valid_appeals)} appeal(s), case number(s): {valid_appeals} is/are assigned to {moderator.id}"
        )
    else:
        messages.append("No valid appeals to mark for review")

    if invalid_appeals:
        errors.append(
            f"{len(invalid_appeals)} appeal(s), case number(s): {invalid_appeals} could not be assigned to {moderator.id} due to internal error. These appeal(s) might already be closed/resolved by concerned moderators"
        )

    if already_assign_appeals:
        errors.append(
            f"{len(already_assign_appeals)} appeal(s), case number(s): {already_assign_appeals} is/are already assigned to a moderator"
        )

    return {
        "message": " ".join(messages),
        "error": "\n".join(errors) if errors else None,
    }


@router.patch("/appeals/{case_number}/check-policy")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def check_appeal_policy(
    case_number: int,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    message = None
    detail = None
    # get the appeal entry
    appeal_entry = admin_service.get_an_appeal(
        case_number=case_number, status_in_list=None, db_session=db
    )
    if not appeal_entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Appeal entry not found"
        )
    if appeal_entry.moderator_id != curr_employee.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )
    if appeal_entry.status == "OPN":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Appeal should be Under Review before policy check",
        )
    if appeal_entry.status in ("ACP", "ACR", "REJ", "RJR"):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Policy check is already done and action has been already taken on this appeal",
        )
    if appeal_entry.status == "CSD":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy check",
        )

    # get the report entry
    report_entry = admin_service.get_a_report_by_report_id_query(
        report_id=str(appeal_entry.report_id), status="RSD", db_session=db
    ).first()
    if not report_entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Report associated with restrict/ban appeal not found",
        )

    # get the restrict ban entry
    restrict_ban_entry = admin_service.get_user_restrict_ban_entry(
        user_id=appeal_entry.user_id, report_id=report_entry.id, db_session=db
    )

    if appeal_entry.content_type == "account" and (
        restrict_ban_entry and restrict_ban_entry.content_type == "account"
    ):
        # get valid flagged content posts
        valid_flagged_content_posts = (
            admin_service.get_all_valid_flagged_content_account_report_id(
                report_id=restrict_ban_entry.report_id, db_session=db
            )
        )
        valid_flagged_content_posts_ids = [
            post[0] for post in valid_flagged_content_posts
        ]

        # check if any post among these have their appeal REJ
        posts_appeal_reject = admin_service.get_all_appeals_content_id_list(
            content_id_list=valid_flagged_content_posts_ids,
            content_type_list=["post"],
            status_in_list=["REJ"],
            db_session=db,
        )
        if posts_appeal_reject:
            appeal_entry.is_policy_followed = False
            message = f"Appeal policy check: Failed. Appeal case number: {case_number}."
            detail = f"Appeals previously linked to {len(posts_appeal_reject)} out of {len(valid_flagged_content_posts_ids)} post(s) associated with the account report is/are already rejected. Hence the appeal for revoking the restriction or ban on account stands rejected."

    elif appeal_entry.content_type == "account" and (
        restrict_ban_entry and restrict_ban_entry.content_type in ("post", "comment")
    ):
        # get the content id from restrict ban entry and query appeal detail table
        # check if there is any REJ appeal against this content
        content_appeal_reject = admin_service.get_a_appeal_report_id_content_id(
            report_id=restrict_ban_entry.report_id,
            content_id=restrict_ban_entry.content_id,
            content_type=["post", "comment"],
            status="REJ",
            db_session=db,
        )
        if content_appeal_reject:
            appeal_entry.is_policy_followed = False
            message = f"Appeal policy check: Failed. Appeal case number: {case_number}"
            detail = f"Appeal previously linked to a {content_appeal_reject.content_type} associated with the account report is already rejected. Hence the appeal for revoking the restriction or ban on account stands rejected."

    elif appeal_entry.content_type == "post" and (
        restrict_ban_entry and restrict_ban_entry.content_type == "account"
    ):
        # get the account id from restrict ban entry and query appeal detail table
        # check if there is any REJ appeal against this account
        account_appeal_reject = admin_service.get_a_appeal_report_id_content_id(
            report_id=restrict_ban_entry.report_id,
            content_id=restrict_ban_entry.content_id,
            content_type=["account"],
            status="REJ",
            db_session=db,
        )
        if account_appeal_reject:
            appeal_entry.is_policy_followed = False
            message = f"Appeal policy check: Failed. Appeal case number: {case_number}"
            detail = "Appeal previously linked to account associated with the post report is already rejected. Hence the appeal for revoking the ban on post stands rejected."

    elif appeal_entry.content_type in ("post", "comment") and (
        restrict_ban_entry and restrict_ban_entry.content_type in ("post", "comment")
    ):
        # get the account id from restrict ban entry and query appeal detail table
        # check if there is any REJ appeal against this account
        account_appeal_reject = admin_service.get_a_appeal_report_id_content_id(
            report_id=restrict_ban_entry.report_id,
            content_id=restrict_ban_entry.user_id,
            content_type=["account"],
            status="REJ",
            db_session=db,
        )
        if account_appeal_reject:
            appeal_entry.is_policy_followed = False
            message = f"Appeal policy check: Failed. Appeal case number: {case_number}"
            detail = f"Appeal previously linked to account associated with the {restrict_ban_entry.content_type} report is already rejected. Hence the appeal for revoking the ban on {restrict_ban_entry.content_type} stands rejected."

    else:
        appeal_entry.is_policy_followed = True
        message = f"Appeal policy check: Success. Appeal case number: {case_number}"
        detail = "Everything in order. Proceed with further action."

    db.commit()

    return {"message": message, "detail": detail}


@router.patch("/appeals/{case_number}/close")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def close_appeal(
    case_number: int,
    close_request: admin_schema.CloseAppeal,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the appeal from case number
    appeal = admin_service.get_an_appeal(case_number, ["CSD", "URV"], db)
    if not appeal:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Appeal to be taken action on, not found",
        )
    if appeal.moderator_id != curr_employee.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )
    if appeal.status == "CSD":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT, detail="Appeal is already closed"
        )

    # if there are any OPN related appeal(s) which were not noticed before, put it/them under review and consider it/them in this action request
    # get open related appeals
    open_related_appeals_to_be_reviewed = (
        admin_service.get_open_appeals_for_specific_content_appeal(
            case_number=case_number,
            content_id=appeal.content_id,
            content_type=appeal.content_type,
            db_session=db,
            moderator_id=appeal.moderator_id,
        )
    )

    # get other related appeals if any then update the status and moderator_note of the related appeals same as the appeal
    related_appeals = admin_service.get_related_appeals_for_specific_appeal(
        case_number=case_number,
        content_id=appeal.content_id,
        content_type=appeal.content_type,
        status="URV",
        moderator_id=curr_employee.id,
        db_session=db,
    ).all()

    open_related_appeals_put_under_review_message = None

    try:
        # update the appeal
        appeal.status = "CSD"
        appeal.moderator_note = close_request.moderator_note

        if open_related_appeals_to_be_reviewed:
            open_related_appeals_case_numbers = [
                related_appeal.case_number
                for related_appeal in open_related_appeals_to_be_reviewed
            ]
            if open_related_appeals_case_numbers:
                valid_appeals = selected_appeals_under_review_update(
                    appeals_request=admin_schema.AppealUnderReviewUpdate(
                        case_number_list=open_related_appeals_case_numbers
                    ),
                    db=db,
                    current_employee=current_employee,
                    is_func_call=True,
                )

                open_related_appeals_put_under_review_message = f"Additional {len(valid_appeals)} related appeal(s), case number(s): {valid_appeals} was/were put under review and was/were processed in this close request"

        if related_appeals:
            for related_report in related_appeals:
                related_report.status = "CSD"
                related_report.moderator_note = close_request.moderator_note

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing close appeal request",
        ) from exc

    moderator_note_full = map_utils.create_appeal_moderator_notes(
        username=appeal.appeal_user.username,
        moderator_note=close_request.moderator_note,
        case_number=case_number,
        content_type=appeal.content_type,
    )

    message = (
        f"Request processed successfully. Appeal case number {case_number} closed."
    )
    if open_related_appeals_put_under_review_message:
        return {
            "message": message,
            "detail": moderator_note_full,
            "additional_message": open_related_appeals_put_under_review_message,
        }

    return {
        "message": message,
        "detail": moderator_note_full,
    }


# api endpoint for appeal accept
@router.post("/appeals/action")
@auth_utils.authorize(["content_admin", "content_mgmt"])
def appeal_action(
    action_request: admin_schema.AppealAction,
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get current employee
    curr_employee = employee_service.get_employee_by_work_email(
        work_email=str(current_employee.email),
        status_not_in_list=["SUP", "TER"],
        db_session=db,
    )

    # get the user
    appeal_user = user_service.get_user_by_username(
        username=action_request.appeal_username,
        status_not_in_list=["PDB", "PDI", "DEL"],
        db_session=db,
    )
    if not appeal_user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Appeal user not found"
        )

    if appeal_user.status == "INA":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Invalid appeal user status",
        )

    # get appeal
    appeal_entry = admin_service.get_an_appeal(
        case_number=action_request.case_number,
        status_in_list=["OPN", "URV", "CSD", "ACP", "ACR", "REJ", "RJR"],
        db_session=db,
    )
    if not appeal_entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Appeal to be taken action on, not found",
        )
    if appeal_entry.moderator_id != curr_employee.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    if appeal_entry.status == "OPN":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Appeal should be under review for action to be taken",
        )
    elif appeal_entry.status == "CSD":
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Appeal to be taken action on, is closed",
        )
    elif appeal_entry.status in ("ACP", "ACR", "REJ", "RJR"):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Action has been already taken on this appeal",
        )

    # check policy done or not
    if appeal_entry.is_policy_followed is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Check appeal policy before appeal action",
        )

    # get report entry
    # get restrict_ban entry associated with the appeal
    # if report entry is absent then it is error
    # for post/comment appeal and post/comment report and restrict ban entry is absent then it is only for unban post/comment
    #   everything with respect to restrict_ban is None
    report_entry = admin_service.get_a_report_by_report_id_query(
        report_id=appeal_entry.report_id, status="RSD", db_session=db
    ).first()
    if not report_entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Report associated with restrict/ban appeal not found",
        )

    restrict_ban_entry = admin_service.get_user_active_restrict_ban_entry_report_id(
        report_id=appeal_entry.report_id, db_session=db
    )
    if (
        report_entry.reported_item_type in ("post", "comment")
        and appeal_entry.content_type in ("post", "comment")
        and not restrict_ban_entry
    ):
        pass
    elif not restrict_ban_entry:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Restrict/ban entry associated with report not found",
        )

    # get other related appeals if any then update the status and moderator_note of the related appeals same as the appeal
    related_appeals_query = admin_service.get_related_appeals_for_specific_appeal(
        case_number=action_request.case_number,
        content_id=appeal_entry.content_id,
        content_type=appeal_entry.content_type,
        status="URV",
        moderator_id=curr_employee.id,
        db_session=db,
    )

    if action_request.action == "accept":
        appeal_entry.status = "ACP"

        # add the appeal accept operations function here
        operation_utils.operations_after_appeal_accept(
            user_id=appeal_entry.user_id,
            report_id=appeal_entry.report_id,
            appeal_content_id=appeal_entry.content_id,
            appeal_content_type=appeal_entry.content_type,
            restrict_ban_content_id=(
                restrict_ban_entry.content_id if restrict_ban_entry else None
            ),
            restrict_ban_content_type=(
                restrict_ban_entry.content_type if restrict_ban_entry else None
            ),
            restrict_ban_status=(
                restrict_ban_entry.status if restrict_ban_entry else None
            ),
            restrict_ban_is_active=(
                restrict_ban_entry.is_active if restrict_ban_entry else None
            ),
            db=db,
        )

        # add related appeals logic
        related_appeals = related_appeals_query.filter(
            admin_model.UserContentRestrictBanAppealDetail.is_policy_followed == True
        ).all()
        if related_appeals:
            for appeal in related_appeals:
                appeal.status = "ACR"
                appeal.moderator_note = action_request.moderator_note

    elif action_request.action == "reject":
        appeal_entry.status = "REJ"

        # add the appeal reject operations function here
        operation_utils.operations_after_accept_reject(
            user_id=appeal_entry.user_id,
            report_id=appeal_entry.report_id,
            appeal_content_id=appeal_entry.content_id,
            appeal_content_type=appeal_entry.content_type,
            restrict_ban_content_id=(
                restrict_ban_entry.content_id if restrict_ban_entry else None
            ),
            restrict_ban_content_type=(
                restrict_ban_entry.content_type if restrict_ban_entry else None
            ),
            restrict_ban_status=(
                restrict_ban_entry.status if restrict_ban_entry else None
            ),
            restrict_ban_enforce_action_at=(
                restrict_ban_entry.enforce_action_at if restrict_ban_entry else None
            ),
            db=db,
        )

        # add related appeals logic
        related_appeals = related_appeals_query.filter(
            admin_model.UserContentRestrictBanAppealDetail.is_policy_followed
            is not None
        ).all()
        if related_appeals:
            for appeal in related_appeals:
                appeal.status = "RJR"
                appeal.moderator_note = action_request.moderator_note
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        print(exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing appeal action request",
        ) from exc

    moderator_note_full = map_utils.create_appeal_moderator_notes(
        username=action_request.appeal_username,
        moderator_note=action_request.moderator_note,
        case_number=action_request.case_number,
        content_type=appeal_entry.content_type,
    )

    message = f"Request processed successfully. Requested action taken on appeal case number {action_request.case_number}."
    return {
        "message": message,
        "detail": moderator_note_full,
    }


@router.get(
    "/users", response_model=dict[str, list[user_schema.AllUsersAdminResponse] | str]
)
@auth_utils.authorize(["management", "software_dev", "content_mgmt", "content_admin"])
def get_users(
    status: (
        Literal[
            "active",
            "inactive",
            "partial_restrict",
            "full_restrict",
            "deactivated",
            "pending_delete",
            "temp_ban",
            "perm_ban",
            "pending_delete_ban",
            "pending_delete_inactive",
            "deleted",
        ]
        | None
    ) = Query(None),
    sort: str | None = Query(None),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # transform status
    try:
        user_status = map_utils.transform_status(value=status) if status else None
    except HTTPException as exc:
        raise exc

    # get users
    all_users = user_service.get_all_users_admin(
        status=user_status, db_session=db, sort=sort
    )
    if not all_users:
        return {"message": "No users yet"}

    return {"users": all_users}


@router.get("/employees")
@auth_utils.authorize(["management", "hr"])
def get_employees(
    status: (
        Literal[
            "active_regular",
            "active_probationary",
            "inactive_emp",
            "terminated",
            "suspended",
        ]
        | None
    ) = None,
    type_: Literal["full_time", "part_time", "contract"] | None = None,
    level: (
        Literal["management", "sofware_dev", "hr", "content_admin", "content_mgmt"]
        | None
    ) = None,
    sort: str | None = Query(None),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # transform status and type
    try:
        employee_status = map_utils.transform_status(value=status) if status else None
        employee_type = map_utils.transform_type(value=type_) if type_ else None
        employee_level = map_utils.transform_access_role(value=level) if level else None
    except HTTPException as exc:
        raise exc

    # get employees
    all_employees = employee_service.get_all_employees_admin(
        status=employee_status,
        type_=employee_type,
        designation_in_list=employee_level,
        sort=sort,
        db_session=db,
    )

    if not all_employees:
        return {"message": "No employees yet"}

    # print(all_employees[0].supervisor)
    all_employees_response = [
        employee_schema.AllEmployeesAdminResponse(
            emp_id=employee.emp_id,
            first_name=employee.first_name,
            last_name=employee.last_name,
            work_email=employee.work_email,
            designation=employee.designation,
            profile_picture=employee.profile_picture,
            personal_email=employee.personal_email,
            date_of_birth=employee.date_of_birth,
            age=employee.age,
            gender=employee.gender,
            join_date=employee.join_date,
            termination_date=employee.termination_date,
            type=employee.type,
            supervisor=employee.supervisor.__dict__ if employee.supervisor else None,
            country_phone_code=employee.country_phone_code,
            phone_number=employee.phone_number,
            aadhaar=employee.aadhaar,
            pan=employee.pan,
            address_line_1=employee.address_line_1,
            address_line_2=employee.address_line_2,
            city=employee.city,
            state_province=employee.state_province,
            zip_postal_code=employee.zip_postal_code,
            country=employee.country,
            status=employee.status,
            created_at=employee.created_at,
        )
        for employee in all_employees
    ]

    return {"employees": all_employees_response}


@router.get("/app-metrics")
@auth_utils.authorize(["management", "software_dev", "content_admin"])
def app_activity_metrics(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db),
    current_employee: auth_schema.AccessTokenPayload = Depends(
        auth_utils.get_current_user
    ),
):
    # get app user metrics
    user_metrics = admin_service.get_app_user_metrics(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get app post metrics
    post_metrics = admin_service.get_app_post_metrics(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get app comment metrics
    comment_metrics = admin_service.get_app_comment_metrics(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get app post like metrics
    post_like_metrics = admin_service.get_app_post_like_metrics(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get app comment like metrics
    comment_like_metrics = admin_service.get_app_comment_like_metrics(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get user(s) with max posts
    users_with_max_posts = admin_service.get_users_with_max_posts(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get user(s) who commented max
    users_who_commented_max = admin_service.get_users_who_commented_max(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get post(s) with max comments
    posts_with_max_comments = admin_service.get_posts_with_max_comments(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get post(s) with max likes
    posts_with_max_likes = admin_service.get_posts_with_max_likes(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get comment(s) with max likes
    comments_with_max_likes = admin_service.get_comments_with_max_likes(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get user(s) with max followers
    users_with_max_followers = admin_service.get_users_with_max_followers(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # get user(s) with max following
    users_with_max_following = admin_service.get_users_with_max_following(
        start_date=start_date, end_date=end_date, db_session=db
    )

    # app activity metrics response
    app_activity_metrics_response = admin_schema.AppActivityMetricsResponse(
        user_metrics=user_metrics,
        post_metrics=post_metrics,
        comment_metrics=comment_metrics,
        post_like_metrics=post_like_metrics,
        comment_like_metrics=comment_like_metrics,
        users_with_max_posts=[
            admin_schema.UsersMaxPosts(
                user=admin_schema.AppMetricsUserOutput(
                    username=user[0], profile_picture=user[1]
                ),
                total_active_posts=user[2],
            )
            for user in users_with_max_posts
        ],
        users_who_commented_max=[
            admin_schema.UsersMaxComments(
                user=admin_schema.AppMetricsUserOutput(
                    username=user[0], profile_picture=user[1]
                ),
                total_active_comments=user[2],
            )
            for user in users_who_commented_max
        ],
        posts_with_max_comments=[
            admin_schema.PostsMaxComments(
                user=admin_schema.AppMetricsUserOutput(
                    username=post[0], profile_picture=post[1]
                ),
                post_id=post[2],
                post_image=post[3],
                post_caption=post[4],
                total_posts_comments=post[5],
                post_datetime=post[6],
            )
            for post in posts_with_max_comments
        ],
        posts_with_max_likes=[
            admin_schema.PostsMaxLikes(
                user=admin_schema.AppMetricsUserOutput(
                    username=post[0], profile_picture=post[1]
                ),
                post_id=post[2],
                post_image=post[3],
                post_caption=post[4],
                total_posts_likes=post[5],
                post_datetime=post[6],
            )
            for post in posts_with_max_likes
        ],
        comments_with_max_likes=[
            admin_schema.CommentsMaxLikes(
                user=admin_schema.AppMetricsUserOutput(
                    username=comment[0], profile_picture=comment[1]
                ),
                comment_id=comment[2],
                comment_content=comment[3],
                total_comment_likes=comment[4],
                comment_datetime=comment[5],
                post_id=comment[6],
            )
            for comment in comments_with_max_likes
        ],
        users_with_max_followers=[
            admin_schema.UsersMaxFollowers(
                user=admin_schema.AppMetricsUserOutput(
                    username=user[0], profile_picture=user[1]
                ),
                total_followers=user[2],
            )
            for user in users_with_max_followers
        ],
        users_with_max_following=[
            admin_schema.UsersMaxFollowing(
                user=admin_schema.AppMetricsUserOutput(
                    username=user[0], profile_picture=user[1]
                ),
                total_following=user[2],
            )
            for user in users_with_max_following
        ],
    )

    return {"app_activity_metrics": app_activity_metrics_response}
