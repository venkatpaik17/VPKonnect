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
