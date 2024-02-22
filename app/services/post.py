from sqlalchemy.orm import Session

from app.models import post as post_model


def get_a_post_query(post_id: str, status_not_in_list: list[str], db_session: Session):
    return db_session.query(post_model.Post).filter(
        post_model.Post.id == post_id,
        post_model.Post.status.notin_(status_not_in_list),
    )


def get_a_post(post_id: str, status_not_in_list: list[str], db_session: Session):
    return get_a_post_query(post_id, status_not_in_list, db_session).first()
