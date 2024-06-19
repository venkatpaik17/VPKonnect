from datetime import timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import post as post_model


def get_a_post_query(post_id: str, status_not_in_list: list[str], db_session: Session):
    return db_session.query(post_model.Post).filter(
        post_model.Post.id == post_id,
        post_model.Post.status.notin_(status_not_in_list),
    )


def get_a_post(post_id: str, status_not_in_list: list[str], db_session: Session):
    return get_a_post_query(post_id, status_not_in_list, db_session).first()


def get_all_posts_by_id_query(
    post_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return db_session.query(post_model.Post).filter(
        post_model.Post.id.in_(post_id_list),
        post_model.Post.status.in_(status_in_list),
        post_model.Post.is_deleted == False,
    )
