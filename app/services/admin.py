from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import admin as admin_model


def get_all_reports_by_status_moderator_id_reported_at(
    status: str,
    db_session: Session,
    moderator_id: str | None,
    reported_at: date | None,
):
    return (
        db_session.query(admin_model.UserContentReportDetail)
        .filter(
            (
                # it will filter with status only if status is not "all", else True which means do not filter using status
                (admin_model.UserContentReportDetail.status == status)
                if status != "all"
                else True
            ),
            (
                (
                    admin_model.UserContentReportDetail.moderator_id == moderator_id
                )  # it will filter with moderator_id only if moderator_id is not None else True which means do not filter using moderator_id
                if moderator_id
                else True
            ),
            (
                (
                    func.date(
                        admin_model.UserContentReportDetail.created_at
                    )  # it will filter with created_at only if status is not None else True which means do not filter using created_at
                    == reported_at
                )
                if reported_at
                else True
            ),
            admin_model.UserContentReportDetail.is_deleted == False,
        )
        .all()
    )


def get_a_report_query(case_number: int, status: str, db_session: Session):
    return db_session.query(admin_model.UserContentReportDetail).filter(
        admin_model.UserContentReportDetail.case_number == case_number,
        admin_model.UserContentReportDetail.status == status,
        admin_model.UserContentReportDetail.is_deleted == False,
    )


def get_a_report(case_number: int, status: str, db_session: Session):
    return get_a_report_query(case_number, status, db_session).first()


def get_open_reports_for_specific_content_report(
    case_number: int,
    reported_item_id: str,
    reported_item_type: str,
    db_session: Session,
):
    return (
        db_session.query(admin_model.UserContentReportDetail)
        .filter(
            admin_model.UserContentReportDetail.case_number != case_number,
            admin_model.UserContentReportDetail.reported_item_id == reported_item_id,
            admin_model.UserContentReportDetail.reported_item_type
            == reported_item_type,
            admin_model.UserContentReportDetail.status == "OPN",
            admin_model.UserContentReportDetail.is_deleted == False,
        )
        .all()
    )


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
        admin_model.GuidelineViolationScore.user_id == user_id
    )


def get_users_guideline_violation_score_query(
    user_id_list: list[UUID], db_session: Session
):
    return db_session.query(admin_model.GuidelineViolationScore).filter(
        admin_model.GuidelineViolationScore.user_id.in_(user_id_list),
    )


def get_user_final_violation_score(user_id: str, db_session: Session):
    return (
        db_session.query(
            admin_model.GuidelineViolationScore.final_violation_score.label("score")
        )
        .filter(admin_model.GuidelineViolationScore.user_id == user_id)
        .first()
    )


def get_all_user_restrict_ban_query(user_id: str, db_session: Session):
    return db_session.query(admin_model.UserRestrictBanDetail).filter(
        admin_model.UserRestrictBanDetail.user_id == user_id,
        admin_model.UserRestrictBanDetail.is_deleted == False,
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
    content_type: str,
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
            admin_model.UserContentRestrictBanAppealDetail.content_type == content_type,
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
