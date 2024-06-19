from uuid import UUID

from sqlalchemy.orm import Session

from app.models import comment as comment_model


def get_a_comment_query(
    comment_id: str, status_not_in_list: list[str], db_session: Session
):
    return db_session.query(comment_model.Comment).filter(
        comment_model.Comment.id == comment_id,
        comment_model.Comment.status.notin_(status_not_in_list),
    )


def get_a_comment(comment_id: str, status_not_in_list: list[str], db_session: Session):
    return get_a_comment_query(comment_id, status_not_in_list, db_session).first()


def get_all_comments_by_id_query(
    comment_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return db_session.query(comment_model.Comment).filter(
        comment_model.Comment.id.in_(comment_id_list),
        comment_model.Comment.status.in_(status_in_list),
        comment_model.Comment.is_deleted == False,
    )
