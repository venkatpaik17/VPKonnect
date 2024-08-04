from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, asc, case, func, or_
from sqlalchemy.orm import Session

from app.models import admin as admin_model
from app.models import comment as comment_model
from app.models import post as post_model
from app.models import user as user_model


def get_all_reports_by_status_moderator_id_reported_at(
    status_in_list: list[str],
    db_session: Session,
    moderator_id: str | None,
    reported_at: date | None,
    type_: str = "assigned",
):
    query = db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.status.in_(status_in_list),
        admin_model.UserContentReportDetail.is_deleted == False,
    )

    if type_ == "new":
        query = query.filter(admin_model.UserContentReportDetail.moderator_id.is_(None))
    elif moderator_id:
        query = query.filter(
            admin_model.UserContentReportDetail.moderator_id == moderator_id
        )

    if reported_at:
        query = query.filter(
            func.date(admin_model.UserContentReportDetail.created_at) == reported_at
        )

    return query.order_by(admin_model.UserContentReportDetail.created_at.asc()).all()


def get_a_report_query(
    case_number: int, status_in_list: list[str] | None, db_session: Session
):
    return db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.case_number == case_number,
        (
            (admin_model.UserContentReportDetail.status.in_(status_in_list))
            if status_in_list
            else True
        ),
        admin_model.UserContentReportDetail.is_deleted == False,
    )


def get_a_report(
    case_number: int, status_in_list: list[str] | None, db_session: Session
):
    return get_a_report_query(case_number, status_in_list, db_session).first()


def get_open_reports_for_specific_content_report(
    case_number: int,
    reported_item_id: str,
    reported_item_type: str,
    report_reason: str | None,
    report_reason_user: UUID | None,
    moderator_id: UUID | None,
    db_session: Session,
):
    query = db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.case_number != case_number,
        admin_model.UserContentReportDetail.reported_item_id == reported_item_id,
        admin_model.UserContentReportDetail.reported_item_type == reported_item_type,
        (
            (admin_model.UserContentReportDetail.report_reason == report_reason)
            if report_reason
            else True
        ),
        (
            (
                admin_model.UserContentReportDetail.report_reason_user_id
                == report_reason_user
            )
            if report_reason_user
            else True
        ),
        admin_model.UserContentReportDetail.status == "OPN",
        admin_model.UserContentReportDetail.is_deleted == False,
    )
    if moderator_id:
        query = query.filter(
            admin_model.UserContentReportDetail.moderator_id == moderator_id
        )
    else:
        query = query.filter(admin_model.UserContentReportDetail.moderator_id.is_(None))

    return query.order_by(admin_model.UserContentReportDetail.created_at.asc()).all()


def get_all_requested_reports_by_case_number_list(
    case_number_list: list[int], db_session: Session
):
    return (
        db_session.query(admin_model.UserContentReportDetail)
        .filter(
            admin_model.UserContentReportDetail.case_number.in_(case_number_list),
            admin_model.UserContentReportDetail.is_deleted == False,
        )
        .all()
    )


def get_a_latest_report_by_content_id_user_id(
    user_id: UUID, content_id: UUID, content_type: str, status: str, db_session: Session
):
    return (
        db_session.query(admin_model.UserContentReportDetail)
        .filter(
            admin_model.UserContentReportDetail.reported_user_id == user_id,
            admin_model.UserContentReportDetail.reported_item_id == content_id,
            admin_model.UserContentReportDetail.reported_item_type == content_type,
            admin_model.UserContentReportDetail.status == status,
            admin_model.UserContentReportDetail.is_deleted == False,
        )
        .order_by(admin_model.UserContentReportDetail.updated_at.desc())
        .first()
    )


def get_a_report_by_report_id_query(report_id: str, status: str, db_session: Session):
    return db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.id == report_id,
        admin_model.UserContentReportDetail.status == status,
        admin_model.UserContentReportDetail.is_deleted == False,
    )


def get_user_guideline_violation_score_query(user_id: str, db_session: Session):
    return db_session.query(admin_model.GuidelineViolationScore).filter(
        admin_model.GuidelineViolationScore.user_id == user_id,
        admin_model.GuidelineViolationScore.is_deleted == False,
    )


def get_users_guideline_violation_score_query(
    user_id_list: list[UUID], db_session: Session
):
    return db_session.query(admin_model.GuidelineViolationScore).filter(
        admin_model.GuidelineViolationScore.user_id.in_(user_id_list),
        admin_model.GuidelineViolationScore.is_deleted == False,
    )


def get_user_final_violation_score(user_id: str, db_session: Session):
    return (
        db_session.query(
            admin_model.GuidelineViolationScore.final_violation_score.label("score")
        )
        .filter(
            admin_model.GuidelineViolationScore.user_id == user_id,
            admin_model.GuidelineViolationScore.is_deleted == False,
        )
        .first()
    )


def get_all_user_restrict_ban_query(user_id: str, db_session: Session):
    return db_session.query(admin_model.UserRestrictBanDetail).filter(
        admin_model.UserRestrictBanDetail.user_id == user_id,
        admin_model.UserRestrictBanDetail.is_deleted == False,
    )


def get_user_restrict_ban_entry(user_id: UUID, report_id: UUID, db_session: Session):
    return (
        db_session.query(admin_model.UserRestrictBanDetail)
        .filter(
            admin_model.UserRestrictBanDetail.user_id == user_id,
            admin_model.UserRestrictBanDetail.report_id == report_id,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .first()
    )


def get_related_reports_for_specific_report_query(
    case_number: int,
    reported_user_id: str,
    reported_item_id: str,
    reported_item_type: str,
    status: str,
    moderator_id: UUID,
    db_session: Session,
):
    return db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.case_number != case_number,
        admin_model.UserContentReportDetail.reported_user_id == reported_user_id,
        admin_model.UserContentReportDetail.reported_item_id == reported_item_id,
        admin_model.UserContentReportDetail.reported_item_type == reported_item_type,
        admin_model.UserContentReportDetail.status == status,
        admin_model.UserContentReportDetail.moderator_id == moderator_id,
        admin_model.UserContentReportDetail.is_deleted == False,
    )


def get_all_reports_reporter_user_id_status(
    reporter_user_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.reporter_user_id.in_(reporter_user_id_list),
        admin_model.UserContentReportDetail.status.in_(status_in_list),
        admin_model.UserContentReportDetail.is_deleted == False,
    )


def get_restricted_users_duration_expired_query(db_session: Session):
    return db_session.query(admin_model.UserRestrictBanDetail).filter(
        admin_model.UserRestrictBanDetail.status.in_(["RSP", "RSF"]),
        admin_model.UserRestrictBanDetail.is_active == True,
        admin_model.UserRestrictBanDetail.is_deleted == False,
        func.now()
        >= (
            admin_model.UserRestrictBanDetail.enforce_action_at
            + (admin_model.UserRestrictBanDetail.duration * timedelta(hours=1))
        ),
    )


def get_temp_banned_users_duration_expired_query(db_session: Session):
    return db_session.query(admin_model.UserRestrictBanDetail).filter(
        admin_model.UserRestrictBanDetail.status.in_(["TBN"]),
        admin_model.UserRestrictBanDetail.is_active == True,
        admin_model.UserRestrictBanDetail.is_deleted == False,
        func.now()
        >= (
            admin_model.UserRestrictBanDetail.enforce_action_at
            + admin_model.UserRestrictBanDetail.duration * timedelta(hours=1)
        ),
    )


# get user active restrict/ban entry
def get_user_active_restrict_ban_entry(user_id: str, db_session: Session):
    return (
        db_session.query(admin_model.UserRestrictBanDetail)
        .filter(
            admin_model.UserRestrictBanDetail.user_id == user_id,
            admin_model.UserRestrictBanDetail.is_active == True,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .first()
    )


# get users active/restrict ban entry
def get_users_active_restrict_ban_entry_query(
    user_id_list: list[UUID] | None, status_in_list: list[str], db_session: Session
):
    return db_session.query(admin_model.UserRestrictBanDetail).filter(
        (
            admin_model.UserRestrictBanDetail.user_id.in_(user_id_list)
            if user_id_list
            else True
        ),
        admin_model.UserRestrictBanDetail.status.in_(status_in_list),
        admin_model.UserRestrictBanDetail.is_active == True,
        admin_model.UserRestrictBanDetail.is_deleted == False,
    )


# get user active restrict/ban entry using userid, reportid
def get_user_active_restrict_ban_entry_user_id_report_id(
    user_id: str, status: str, report_id: str, db_session: Session
):
    return (
        db_session.query(admin_model.UserRestrictBanDetail)
        .filter(
            admin_model.UserRestrictBanDetail.user_id == user_id,
            admin_model.UserRestrictBanDetail.status == status,
            admin_model.UserRestrictBanDetail.report_id == report_id,
            admin_model.UserRestrictBanDetail.is_active == True,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .first()
    )


# get users active restrict/ban entries using id
def get_users_active_restrict_ban_entry_id(
    restrict_ban_id_list: list[UUID], db_session: Session
):
    return (
        db_session.query(admin_model.UserRestrictBanDetail)
        .filter(
            admin_model.UserRestrictBanDetail.id.in_(restrict_ban_id_list),
            admin_model.UserRestrictBanDetail.is_active == True,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .all()
    )


def get_user_active_restrict_ban_entry_report_id(report_id: UUID, db_session: Session):
    return (
        db_session.query(admin_model.UserRestrictBanDetail)
        .filter(
            admin_model.UserRestrictBanDetail.report_id == report_id,
            admin_model.UserRestrictBanDetail.is_active == True,
            admin_model.UserRestrictBanDetail.is_deleted == False,
        )
        .first()
    )


# get last_added_score
def get_last_added_score(
    score_id: str, report_id: str, db_session: Session, is_added: bool = True
):
    return (
        db_session.query(admin_model.GuidelineViolationLastAddedScore)
        .filter(
            admin_model.GuidelineViolationLastAddedScore.score_id == score_id,
            admin_model.GuidelineViolationLastAddedScore.report_id == report_id,
            admin_model.GuidelineViolationLastAddedScore.is_removed == False,
            admin_model.GuidelineViolationLastAddedScore.is_deleted == False,
            admin_model.GuidelineViolationLastAddedScore.is_added == is_added,
        )
        .first()
    )


def get_all_valid_flagged_content_account_report_id(
    report_id: UUID, db_session: Session
):
    return (
        db_session.query(admin_model.AccountReportFlaggedContent.valid_flagged_content)
        .filter(
            admin_model.AccountReportFlaggedContent.report_id == report_id,
            admin_model.AccountReportFlaggedContent.is_deleted == False,
        )
        .all()
    )


def get_account_report_flagged_content_entry_valid_flagged_content_id(
    content_id: UUID, db_session: Session
):
    return (
        db_session.query(admin_model.AccountReportFlaggedContent)
        .filter(
            admin_model.AccountReportFlaggedContent.valid_flagged_content == content_id,
            admin_model.AccountReportFlaggedContent.is_deleted == False,
        )
        .first()
    )


def check_permanent_ban_appeal_limit_expiry_query(db_session: Session):
    return db_session.query(admin_model.UserRestrictBanDetail).filter(
        admin_model.UserRestrictBanDetail.status == "PBN",
        func.now()
        >= (admin_model.UserRestrictBanDetail.enforce_action_at + timedelta(days=21)),
        admin_model.UserRestrictBanDetail.is_active == True,
        admin_model.UserRestrictBanDetail.is_deleted == False,
    )


def get_appeals_by_id(appeal_id_list: list[UUID], db_session: Session):
    return (
        db_session.query(admin_model.UserContentRestrictBanAppealDetail)
        .filter(
            admin_model.UserContentRestrictBanAppealDetail.id.in_(appeal_id_list),
            admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
        )
        .all()
    )


def get_a_appeal_report_id_content_id(
    report_id: UUID | None,
    content_id: UUID,
    content_type: list[str],
    status: str,
    db_session: Session,
):
    return (
        db_session.query(admin_model.UserContentRestrictBanAppealDetail)
        .filter(
            (
                (admin_model.UserContentRestrictBanAppealDetail.report_id == report_id)
                if report_id
                else True
            ),
            admin_model.UserContentRestrictBanAppealDetail.content_id == content_id,
            admin_model.UserContentRestrictBanAppealDetail.content_type.in_(
                content_type
            ),
            admin_model.UserContentRestrictBanAppealDetail.status == status,
            admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
        )
        .first()
    )


def get_all_appeals_report_id_list_query(
    report_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return db_session.query(admin_model.UserContentRestrictBanAppealDetail).filter(
        admin_model.UserContentRestrictBanAppealDetail.report_id.in_(report_id_list),
        admin_model.UserContentRestrictBanAppealDetail.status.in_(status_in_list),
        admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
    )


def get_all_appeals_report_id_list(
    report_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return get_all_appeals_report_id_list_query(
        report_id_list, status_in_list, db_session
    ).all()


def get_all_appeals_report_id_content_type_list(
    report_id_list: list[UUID],
    status_in_list: list[str],
    content_type: str,
    db_session: Session,
):
    return (
        db_session.query(admin_model.UserContentRestrictBanAppealDetail)
        .filter(
            admin_model.UserContentRestrictBanAppealDetail.report_id.in_(
                report_id_list
            ),
            admin_model.UserContentRestrictBanAppealDetail.status.in_(status_in_list),
            admin_model.UserContentRestrictBanAppealDetail.content_type == content_type,
            admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
        )
        .all()
    )


def get_all_appeals_content_id_list(
    content_id_list: list[UUID] | None,
    content_type_list: list[str],
    status_in_list: list[str],
    db_session: Session,
):
    return (
        db_session.query(admin_model.UserContentRestrictBanAppealDetail)
        .filter(
            (
                admin_model.UserContentRestrictBanAppealDetail.content_id.in_(
                    content_id_list
                )
                if content_id_list
                else True
            ),
            admin_model.UserContentRestrictBanAppealDetail.content_type.in_(
                content_type_list
            ),
            admin_model.UserContentRestrictBanAppealDetail.status.in_(status_in_list),
            admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
        )
        .all()
    )


def get_all_appeals_by_status_moderator_id_reported_at(
    status_in_list: list[str],
    db_session: Session,
    moderator_id: str | None,
    reported_at: date | None,
    type_: str = "assigned",
):
    query = db_session.query(admin_model.UserContentRestrictBanAppealDetail).filter(
        admin_model.UserContentRestrictBanAppealDetail.status.in_(status_in_list),
        admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
    )

    if type_ == "new":
        query = query.filter(
            admin_model.UserContentRestrictBanAppealDetail.moderator_id.is_(None)
        )
    elif moderator_id:
        query = query.filter(
            admin_model.UserContentRestrictBanAppealDetail.moderator_id == moderator_id
        )

    if reported_at:
        query = query.filter(
            func.date(admin_model.UserContentRestrictBanAppealDetail.created_at)
            == reported_at
        )

    return query.order_by(
        admin_model.UserContentRestrictBanAppealDetail.created_at.asc()
    ).all()


def get_an_appeal_query(
    case_number: int, status_in_list: list[str] | None, db_session: Session
):
    return db_session.query(admin_model.UserContentRestrictBanAppealDetail).filter(
        admin_model.UserContentRestrictBanAppealDetail.case_number == case_number,
        (
            (admin_model.UserContentRestrictBanAppealDetail.status.in_(status_in_list))
            if status_in_list
            else True
        ),
        admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
    )


def get_an_appeal(
    case_number: int, status_in_list: list[str] | None, db_session: Session
):
    return get_an_appeal_query(case_number, status_in_list, db_session).first()


def get_open_appeals_for_specific_content_appeal(
    case_number: int,
    content_id: UUID,
    content_type: str,
    db_session: Session,
    moderator_id: UUID | None,
):
    query = db_session.query(admin_model.UserContentRestrictBanAppealDetail).filter(
        admin_model.UserContentRestrictBanAppealDetail.case_number != case_number,
        admin_model.UserContentRestrictBanAppealDetail.content_id == content_id,
        admin_model.UserContentRestrictBanAppealDetail.content_type == content_type,
        admin_model.UserContentRestrictBanAppealDetail.status == "OPN",
        admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
    )
    if moderator_id:
        query = query.filter(
            admin_model.UserContentRestrictBanAppealDetail.moderator_id == moderator_id
        )
    else:
        query = query.filter(
            admin_model.UserContentRestrictBanAppealDetail.moderator_id.is_(None)
        )

    return query.order_by(
        admin_model.UserContentRestrictBanAppealDetail.created_at.asc()
    ).all()


def get_related_appeals_for_specific_appeal(
    case_number: int,
    content_id: str,
    content_type: str,
    status: str,
    moderator_id: UUID,
    db_session: Session,
):
    return db_session.query(admin_model.UserContentRestrictBanAppealDetail).filter(
        admin_model.UserContentRestrictBanAppealDetail.case_number != case_number,
        admin_model.UserContentRestrictBanAppealDetail.content_id == content_id,
        admin_model.UserContentRestrictBanAppealDetail.content_type == content_type,
        admin_model.UserContentRestrictBanAppealDetail.status == status,
        admin_model.UserContentRestrictBanAppealDetail.moderator_id == moderator_id,
        admin_model.UserContentRestrictBanAppealDetail.is_deleted == False,
    )


# get user violation details
def get_user_violation_details(user_id: UUID, db_session: Session):
    query = (
        db_session.query(
            func.count(
                case(
                    [
                        (
                            and_(
                                admin_model.UserRestrictBanDetail.id.is_(None),
                                admin_model.UserContentReportDetail.reported_item_type
                                == "post",
                                admin_model.UserContentReportDetail.status.in_(
                                    ["RSD", "FRS"]
                                ),
                            ),
                            admin_model.UserContentReportDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_post_violations_no_restrict_ban"),
            func.count(
                case(
                    [
                        (
                            and_(
                                admin_model.UserRestrictBanDetail.id.is_(None),
                                admin_model.UserContentReportDetail.reported_item_type
                                == "comment",
                                admin_model.UserContentReportDetail.status.in_(
                                    ["RSD", "FRS"]
                                ),
                            ),
                            admin_model.UserContentReportDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_comment_violations_no_restrict_ban"),
            func.count(
                case(
                    [
                        (
                            and_(
                                admin_model.UserRestrictBanDetail.id.is_(None),
                                admin_model.UserContentReportDetail.reported_item_type
                                == "account",
                                admin_model.UserContentReportDetail.status.in_(
                                    ["RSD", "FRS"]
                                ),
                            ),
                            admin_model.UserContentReportDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_account_violations_no_restrict_ban"),
            func.count(
                case(
                    [
                        (
                            admin_model.UserRestrictBanDetail.id.is_(None),
                            admin_model.UserContentReportDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("total_num_of_violations_no_restrict_ban"),
            func.count(
                case(
                    [
                        (
                            admin_model.UserRestrictBanDetail.status == "RSP",
                            admin_model.UserRestrictBanDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_partial_account_restrictions"),
            func.count(
                case(
                    [
                        (
                            admin_model.UserRestrictBanDetail.status == "RSF",
                            admin_model.UserRestrictBanDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_full_account_restrictions"),
            func.count(
                case(
                    [
                        (
                            admin_model.UserRestrictBanDetail.status == "TBN",
                            admin_model.UserRestrictBanDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_account_temporary_bans"),
            func.count(
                case(
                    [
                        (
                            admin_model.UserRestrictBanDetail.status == "PBN",
                            admin_model.UserRestrictBanDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("num_of_account_permanent_bans"),
            func.count(
                case(
                    [
                        (
                            admin_model.UserRestrictBanDetail.id.is_not(None),
                            admin_model.UserRestrictBanDetail.id,
                        )
                    ],
                    else_=None,
                )
            ).label("total_num_of_account_restrict_bans"),
        )
        .join(
            admin_model.UserRestrictBanDetail,
            admin_model.UserContentReportDetail.id
            == admin_model.UserRestrictBanDetail.report_id,
            isouter=True,
        )
        .filter(
            and_(
                admin_model.UserContentReportDetail.reported_user_id == user_id,
                admin_model.UserContentReportDetail.is_deleted == (False),
                or_(
                    admin_model.UserRestrictBanDetail.id.is_(None),
                    admin_model.UserRestrictBanDetail.is_deleted == (False),
                ),
            )
        )
    )

    return query.one()


def get_app_user_metrics(
    start_date: date | None, end_date: date | None, db_session: Session
):
    subquery = db_session.query(
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Added",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_added"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Active",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_active"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Inactive",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_inactive"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric
                            == "Users_Restricted_Partial",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_restricted_partial"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric
                            == "Users_Restricted_Full",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_restricted_full"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Deactivated",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_deactivated"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Pending_Delete",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_pending_delete"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Banned_Temp",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_banned_temp"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Banned_Perm",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_banned_perm"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric
                            == "Users_Unrestricted_Partial",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_unrestricted_partial"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric
                            == "Users_Unrestricted_Full",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_unrestricted_full"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Unbanned_Temp",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_unbanned_temp"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Unbanned_Perm",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_unbanned_perm"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Reactivated",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_reactivated"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Restored",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_restored"),
        func.coalesce(
            func.sum(
                case(
                    [
                        (
                            admin_model.ActivityDetail.metric == "Users_Deleted",
                            admin_model.ActivityDetail.count,
                        )
                    ],
                    else_=0,
                )
            ),
            0,
        ).label("users_deleted"),
    ).subquery()

    query = db_session.query(
        subquery.c.users_added,
        (subquery.c.users_added - subquery.c.users_active).label("users_unverified"),
        subquery.c.users_active,
        subquery.c.users_inactive,
        subquery.c.users_restricted_partial,
        subquery.c.users_restricted_full,
        subquery.c.users_deactivated,
        subquery.c.users_pending_delete,
        subquery.c.users_banned_temp,
        subquery.c.users_banned_perm,
        subquery.c.users_unrestricted_partial,
        subquery.c.users_unrestricted_full,
        subquery.c.users_unbanned_temp,
        subquery.c.users_unbanned_perm,
        subquery.c.users_reactivated,
        subquery.c.users_restored,
        subquery.c.users_deleted,
    )

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            admin_model.ActivityDetail.date.between(start_date, end_date)
        )
    elif start_date:
        query = query.filter(admin_model.ActivityDetail.date >= start_date)
    elif end_date:
        query = query.filter(admin_model.ActivityDetail.date <= end_date)

    return query.one()


def get_app_post_metrics(
    start_date: date | None, end_date: date | None, db_session: Session
):
    query = db_session.query(
        func.count(post_model.Post.id).label("total_added_posts"),
        func.count(
            case([(and_(post_model.Post.is_deleted == False), post_model.Post.id)])
        ).label("total_available_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "PUB",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("active_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "DRF",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("draft_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "HID",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("hidden_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "FLB",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("flagged_to_be_banned_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "BAN",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("banned_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "FLD",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("flagged_deleted_posts"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.Post.status == "RMV",
                            post_model.Post.is_deleted == False,
                        ),
                        post_model.Post.id,
                    )
                ]
            )
        ).label("removed_posts"),
    )

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            func.date(post_model.Post.created_at).between(start_date, end_date)
        )
    elif start_date:
        query = query.filter(func.date(post_model.Post.created_at) >= start_date)
    elif end_date:
        query = query.filter(func.date(post_model.Post.created_at) <= end_date)

    return query.one()


def get_app_comment_metrics(
    start_date: date | None, end_date: date | None, db_session: Session
):
    query = db_session.query(
        func.count(comment_model.Comment.id).label("total_added_comments"),
        func.count(
            case(
                [(comment_model.Comment.is_deleted == False, comment_model.Comment.id)]
            )
        ).label("total_available_comments"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.Comment.status == "PUB",
                            comment_model.Comment.is_deleted == False,
                        ),
                        comment_model.Comment.id,
                    )
                ]
            )
        ).label("active_comments"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.Comment.status == "HID",
                            comment_model.Comment.is_deleted == False,
                        ),
                        comment_model.Comment.id,
                    )
                ]
            )
        ).label("hidden_comments"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.Comment.status == "FLB",
                            comment_model.Comment.is_deleted == False,
                        ),
                        comment_model.Comment.id,
                    )
                ]
            )
        ).label("flagged_to_be_banned_comments"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.Comment.status == "BAN",
                            comment_model.Comment.is_deleted == False,
                        ),
                        comment_model.Comment.id,
                    )
                ]
            )
        ).label("banned_comments"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.Comment.status == "FLD",
                            comment_model.Comment.is_deleted == False,
                        ),
                        comment_model.Comment.id,
                    )
                ]
            )
        ).label("flagged_deleted_comments"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.Comment.status == "RMV",
                            comment_model.Comment.is_deleted == False,
                        ),
                        comment_model.Comment.id,
                    )
                ]
            )
        ).label("removed_comments"),
    )

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            func.date(comment_model.Comment.created_at).between(start_date, end_date)
        )
    elif start_date:
        query = query.filter(func.date(comment_model.Comment.created_at) >= start_date)
    elif end_date:
        query = query.filter(func.date(comment_model.Comment.created_at) <= end_date)

    return query.one()


def get_app_post_like_metrics(
    start_date: date | None, end_date: date | None, db_session: Session
):
    query = db_session.query(
        func.count(
            case(
                [
                    (
                        post_model.PostLike.status.in_(["ACT", "HID"]),
                        post_model.PostLike.id,
                    )
                ]
            )
        ).label("total_likes"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.PostLike.status.in_(["ACT", "HID"]),
                            post_model.PostLike.is_deleted == False,
                        ),
                        post_model.PostLike.id,
                    )
                ]
            )
        ).label("total_available_likes"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.PostLike.status == "ACT",
                            post_model.PostLike.is_deleted == False,
                        ),
                        post_model.PostLike.id,
                    )
                ]
            )
        ).label("active_likes"),
        func.count(
            case(
                [
                    (
                        and_(
                            post_model.PostLike.status == "HID",
                            post_model.PostLike.is_deleted == False,
                        ),
                        post_model.PostLike.id,
                    )
                ]
            )
        ).label("hidden_likes"),
    )

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            func.date(post_model.PostLike.created_at).between(start_date, end_date)
        )
    elif start_date:
        query = query.filter(func.date(post_model.PostLike.created_at) >= start_date)
    elif end_date:
        query = query.filter(func.date(post_model.PostLike.created_at) <= end_date)

    return query.one()


def get_app_comment_like_metrics(
    start_date: date | None, end_date: date | None, db_session: Session
):
    query = db_session.query(
        func.count(
            case(
                [
                    (
                        comment_model.CommentLike.status.in_(["ACT", "HID"]),
                        comment_model.CommentLike.id,
                    )
                ]
            )
        ).label("total_likes"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.CommentLike.status.in_(["ACT", "HID"]),
                            comment_model.CommentLike.is_deleted == False,
                        ),
                        comment_model.CommentLike.id,
                    )
                ]
            )
        ).label("total_available_likes"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.CommentLike.status == "ACT",
                            comment_model.CommentLike.is_deleted == False,
                        ),
                        comment_model.CommentLike.id,
                    )
                ]
            )
        ).label("active_likes"),
        func.count(
            case(
                [
                    (
                        and_(
                            comment_model.CommentLike.status == "HID",
                            comment_model.CommentLike.is_deleted == False,
                        ),
                        comment_model.CommentLike.id,
                    )
                ]
            )
        ).label("hidden_likes"),
    )

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            func.date(comment_model.CommentLike.created_at).between(
                start_date, end_date
            )
        )
    elif start_date:
        query = query.filter(
            func.date(comment_model.CommentLike.created_at) >= start_date
        )
    elif end_date:
        query = query.filter(
            func.date(comment_model.CommentLike.created_at) <= end_date
        )

    return query.one()


def get_users_with_max_posts(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query
    query = db_session.query(
        post_model.Post.user_id, func.count(post_model.Post.id).label("cnt")
    ).filter(post_model.Post.status == "PUB")

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            func.date(post_model.Post.created_at).between(start_date, end_date)
        )
    elif start_date:
        query = query.filter(func.date(post_model.Post.created_at) >= start_date)
    elif end_date:
        query = query.filter(func.date(post_model.Post.created_at) <= end_date)

    # Define the subquery to get the count of active posts per user
    subquery = query.group_by(post_model.Post.user_id).subquery()

    # Define the subquery to get the maximum count of active posts
    max_count_subquery = db_session.query(
        func.max(subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get users with the maximum count
    filtered_subquery = (
        db_session.query(subquery.c.user_id, subquery.c.cnt.label("total_active_posts"))
        .filter(subquery.c.cnt == max_count_subquery)
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        filtered_subquery.c.total_active_posts,
    ).join(filtered_subquery, user_model.User.id == filtered_subquery.c.user_id)

    return main_query.all()


def get_users_who_commented_max(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query
    query = db_session.query(
        comment_model.Comment.user_id, func.count(comment_model.Comment.id).label("cnt")
    ).filter(comment_model.Comment.status == "PUB")

    # Apply date filters if specified
    if start_date and end_date:
        query = query.filter(
            func.date(comment_model.Comment.created_at).between(start_date, end_date)
        )
    elif start_date:
        query = query.filter(func.date(comment_model.Comment.created_at) >= start_date)
    elif end_date:
        query = query.filter(func.date(comment_model.Comment.created_at) <= end_date)

    # Define the subquery to get the count of active comments per user
    subquery = query.group_by(comment_model.Comment.user_id).subquery()

    # Define the subquery to get the maximum count of active comments
    max_count_subquery = db_session.query(
        func.max(subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get users with the maximum count
    filtered_subquery = (
        db_session.query(
            subquery.c.user_id, subquery.c.cnt.label("total_active_comments")
        )
        .filter(subquery.c.cnt == max_count_subquery)
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        filtered_subquery.c.total_active_comments,
    ).join(filtered_subquery, user_model.User.id == filtered_subquery.c.user_id)

    return main_query.all()


def get_posts_with_max_comments(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query for comments count
    comment_query = db_session.query(
        comment_model.Comment.post_id, func.count(comment_model.Comment.id).label("cnt")
    ).filter(comment_model.Comment.status == "PUB")

    # Apply date filters if specified
    if start_date and end_date:
        comment_query = comment_query.filter(
            func.date(comment_model.Comment.created_at).between(start_date, end_date)
        )
    elif start_date:
        comment_query = comment_query.filter(
            func.date(comment_model.Comment.created_at) >= start_date
        )
    elif end_date:
        comment_query = comment_query.filter(
            func.date(comment_model.Comment.created_at) <= end_date
        )

    # Define the subquery to get the count of active comments per post
    subquery = comment_query.group_by(comment_model.Comment.post_id).subquery()

    # Define the subquery to get the maximum count of active comments
    max_count_subquery = db_session.query(
        func.max(subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get posts with the maximum count
    filtered_subquery = (
        db_session.query(
            subquery.c.post_id, subquery.c.cnt.label("total_active_comments")
        )
        .filter(subquery.c.cnt == max_count_subquery)
        .subquery()
    )

    # Define the subquery to get post details
    post_details_subquery = (
        db_session.query(
            post_model.Post.id,
            post_model.Post.user_id,
            post_model.Post.image,
            post_model.Post.caption,
            post_model.Post.created_at,
            filtered_subquery.c.total_active_comments,
        )
        .join(filtered_subquery, post_model.Post.id == filtered_subquery.c.post_id)
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        post_details_subquery.c.id.label("post_id"),
        post_details_subquery.c.image.label("post_image"),
        post_details_subquery.c.caption.label("post_caption"),
        post_details_subquery.c.total_active_comments,
        post_details_subquery.c.created_at.label("post_datetime"),
    ).join(post_details_subquery, user_model.User.id == post_details_subquery.c.user_id)

    return main_query.all()


def get_posts_with_max_likes(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query for likes count
    like_query = (
        db_session.query(
            post_model.PostLike.post_id, func.count(post_model.PostLike.id).label("cnt")
        )
        .join(post_model.Post, post_model.Post.id == post_model.PostLike.post_id)
        .filter(post_model.Post.status == "PUB", post_model.PostLike.status == "ACT")
    )

    # Apply date filters if specified
    if start_date and end_date:
        like_query = like_query.filter(
            func.date(post_model.Post.created_at).between(start_date, end_date)
        )
    elif start_date:
        like_query = like_query.filter(
            func.date(post_model.Post.created_at) >= start_date
        )
    elif end_date:
        like_query = like_query.filter(
            func.date(post_model.Post.created_at) <= end_date
        )

    # Define the subquery to get the count of active likes per post
    subquery = like_query.group_by(post_model.PostLike.post_id).subquery()

    # Define the subquery to get the maximum count of active likes
    max_count_subquery = db_session.query(
        func.max(subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get posts with the maximum count
    filtered_subquery = (
        db_session.query(subquery.c.post_id, subquery.c.cnt.label("total_active_likes"))
        .filter(subquery.c.cnt == max_count_subquery)
        .subquery()
    )

    # Define the subquery to get post details
    post_details_subquery = (
        db_session.query(
            post_model.Post.id,
            post_model.Post.user_id,
            post_model.Post.image,
            post_model.Post.caption,
            post_model.Post.created_at,
            filtered_subquery.c.total_active_likes,
        )
        .join(filtered_subquery, post_model.Post.id == filtered_subquery.c.post_id)
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        post_details_subquery.c.id.label("post_id"),
        post_details_subquery.c.image.label("post_image"),
        post_details_subquery.c.caption.label("post_caption"),
        post_details_subquery.c.total_active_likes.label("total_post_likes"),
        post_details_subquery.c.created_at.label("post_datetime"),
    ).join(post_details_subquery, user_model.User.id == post_details_subquery.c.user_id)

    return main_query.all()


def get_comments_with_max_likes(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query for likes count
    like_query = (
        db_session.query(
            comment_model.CommentLike.comment_id,
            func.count(comment_model.CommentLike.id).label("cnt"),
        )
        .join(
            comment_model.Comment,
            comment_model.Comment.id == comment_model.CommentLike.comment_id,
        )
        .filter(
            comment_model.Comment.status == "PUB",
            comment_model.CommentLike.status == "ACT",
        )
    )

    if start_date and end_date:
        like_query = like_query.filter(
            func.date(comment_model.Comment.created_at).between(start_date, end_date)
        )
    elif start_date:
        like_query = like_query.filter(
            func.date(comment_model.Comment.created_at) >= start_date
        )
    elif end_date:
        like_query = like_query.filter(
            func.date(comment_model.Comment.created_at) <= end_date
        )

    # Define the subquery to get the count of active likes per comment
    subquery = like_query.group_by(comment_model.CommentLike.comment_id).subquery()

    # Define the subquery to get the maximum count of active likes
    max_count_subquery = db_session.query(
        func.max(subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get comments with the maximum count
    filtered_subquery = (
        db_session.query(
            subquery.c.comment_id, subquery.c.cnt.label("total_active_likes")
        )
        .filter(subquery.c.cnt == max_count_subquery)
        .subquery()
    )

    # Define the subquery to get comment details
    comment_details_subquery = (
        db_session.query(
            comment_model.Comment.id,
            comment_model.Comment.user_id,
            comment_model.Comment.post_id,
            comment_model.Comment.content,
            comment_model.Comment.created_at,
            filtered_subquery.c.total_active_likes,
        )
        .join(
            filtered_subquery,
            comment_model.Comment.id == filtered_subquery.c.comment_id,
        )
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        comment_details_subquery.c.id.label("comment_id"),
        comment_details_subquery.c.content.label("comment_content"),
        comment_details_subquery.c.total_active_likes.label("total_comment_likes"),
        comment_details_subquery.c.created_at.label("comment_datetime"),
        comment_details_subquery.c.post_id,
    ).join(
        comment_details_subquery,
        user_model.User.id == comment_details_subquery.c.user_id,
    )

    return main_query.all()


def get_users_with_max_followers(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query for followers count with optional date filtering
    base_query = db_session.query(
        user_model.UserFollowAssociation.followed_user_id,
        func.count(user_model.UserFollowAssociation.follower_user_id).label("cnt"),
    ).filter(user_model.UserFollowAssociation.status == "ACP")

    # Apply date filtering if applicable
    if start_date and end_date:
        base_query = base_query.filter(
            func.date(user_model.UserFollowAssociation.created_at).between(
                start_date, end_date
            )
        )
    elif start_date:
        base_query = base_query.filter(
            func.date(user_model.UserFollowAssociation.created_at) >= start_date
        )
    elif end_date:
        base_query = base_query.filter(
            func.date(user_model.UserFollowAssociation.created_at) <= end_date
        )

    # Use a subquery to get the maximum count of followers
    base_subquery = base_query.group_by(
        user_model.UserFollowAssociation.followed_user_id
    ).subquery()

    # Define the subquery to get the maximum count of followers
    max_followers_subquery = db_session.query(
        func.max(base_subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get users with the maximum followers
    filtered_followers_subquery = (
        db_session.query(
            base_subquery.c.followed_user_id,
            base_subquery.c.cnt.label("total_followers"),
        )
        .filter(base_subquery.c.cnt == max_followers_subquery)
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        filtered_followers_subquery.c.total_followers,
    ).join(
        filtered_followers_subquery,
        user_model.User.id == filtered_followers_subquery.c.followed_user_id,
    )

    return main_query.all()


def get_users_with_max_following(
    start_date: date | None, end_date: date | None, db_session: Session
):
    # Build the base query for following count with optional date filtering
    base_query = db_session.query(
        user_model.UserFollowAssociation.follower_user_id,
        func.count(user_model.UserFollowAssociation.followed_user_id).label("cnt"),
    ).filter(user_model.UserFollowAssociation.status == "ACP")

    # Apply date filtering if applicable
    if start_date and end_date:
        base_query = base_query.filter(
            func.date(user_model.UserFollowAssociation.created_at).between(
                start_date, end_date
            )
        )
    elif start_date:
        base_query = base_query.filter(
            func.date(user_model.UserFollowAssociation.created_at) >= start_date
        )
    elif end_date:
        base_query = base_query.filter(
            func.date(user_model.UserFollowAssociation.created_at) <= end_date
        )

    # Use a subquery to get the maximum count of followings
    base_subquery = base_query.group_by(
        user_model.UserFollowAssociation.follower_user_id
    ).subquery()

    # Define the subquery to get the maximum count of followings
    max_following_subquery = db_session.query(
        func.max(base_subquery.c.cnt).label("max_cnt")
    ).scalar_subquery()

    # Define the filtered subquery to get users with the maximum followings
    filtered_followings_subquery = (
        db_session.query(
            base_subquery.c.follower_user_id,
            base_subquery.c.cnt.label("total_following"),
        )
        .filter(base_subquery.c.cnt == max_following_subquery)
        .subquery()
    )

    # Define the main query to join with the User table
    main_query = db_session.query(
        user_model.User.username,
        user_model.User.profile_picture,
        filtered_followings_subquery.c.total_following,
    ).join(
        filtered_followings_subquery,
        user_model.User.id == filtered_followings_subquery.c.follower_user_id,
    )

    return main_query.all()
