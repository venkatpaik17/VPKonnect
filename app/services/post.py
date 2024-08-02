from datetime import timedelta
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models import post as post_model
from app.models import user as user_model


def get_a_post_query(post_id: str, status_not_in_list: list[str], db_session: Session):
    return db_session.query(post_model.Post).filter(
        post_model.Post.id == post_id,
        post_model.Post.status.notin_(status_not_in_list),
        post_model.Post.is_deleted == False,
        post_model.Post.is_ban_final == False,
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
        post_model.Post.is_ban_final == False,
    )


def count_posts(user_id: UUID, status: str, db_session: Session):
    return (
        db_session.query(func.count(post_model.Post.id))
        .filter(
            post_model.Post.user_id == user_id,
            post_model.Post.status == status,
            post_model.Post.is_deleted == False,
            post_model.Post.is_ban_final == False,
        )
        .scalar()
    )


def get_all_posts_profile(
    profile_user_id: UUID,
    status: str,
    limit: int,
    last_post_id: UUID | None,
    db_session: Session,
    is_ban_final: bool = False,
):
    query = db_session.query(post_model.Post).filter(
        post_model.Post.user_id == profile_user_id,
        post_model.Post.status == status,
        post_model.Post.is_ban_final == is_ban_final,
        post_model.Post.is_deleted == False,
    )

    if last_post_id:
        query = query.filter(post_model.Post.id < last_post_id)

    return query.order_by(post_model.Post.id.desc()).limit(limit).all()


def count_post_likes(post_id: UUID, status: str, db_session: Session):
    return (
        db_session.query(func.count(post_model.PostLike.id))
        .filter(
            post_model.PostLike.id == post_id,
            post_model.PostLike.status == status,
            post_model.PostLike.is_deleted == False,
        )
        .scalar()
    )


def get_all_posts_user_feed(
    followed_user_id_list: list[UUID],
    last_seen_post_id: UUID | None,
    limit: int,
    db_session: Session,
):
    query = db_session.query(post_model.Post).filter(
        post_model.Post.user_id.in_(followed_user_id_list),
        post_model.Post.status == "PUB",
        post_model.Post.created_at >= func.now() - timedelta(days=3),
        post_model.Post.is_ban_final == False,
        post_model.Post.is_deleted == False,
    )

    if last_seen_post_id:
        query = query.filter(post_model.Post.id < last_seen_post_id)

    results = query.order_by(post_model.Post.id.desc()).limit(limit).all()
    next_last_seen_post_id = results[-1].id if results else None

    return results, next_last_seen_post_id


def user_like_exists_query(user_id: UUID, post_id: UUID, db_session: Session):
    return db_session.query(post_model.PostLike).filter(
        post_model.PostLike.user_id == user_id,
        post_model.PostLike.post_id == post_id,
        post_model.PostLike.status == "ACT",
        post_model.PostLike.is_deleted == False,
    )


def user_like_exists(user_id: UUID, post_id: UUID, db_session: Session):
    return user_like_exists_query(user_id, post_id, db_session).first()


def get_post_like_users(
    curr_user_id: UUID,
    post_id: UUID,
    limit: int,
    last_like_user_id: UUID | None,
    db_session: Session,
):
    # subquery for getting following of curr user
    user_following_subq = (
        select([user_model.UserFollowAssociation.followed_user_id])
        .where(
            user_model.UserFollowAssociation.follower_user_id == curr_user_id,
            user_model.UserFollowAssociation.is_deleted == False,
        )
        .subquery()
    )

    stmt = (
        select(
            [
                user_model.User.id,
                user_model.User.profile_picture,
                user_model.User.username,
                exists(
                    select([1]).where(
                        user_following_subq.c.followed_user_id == user_model.User.id
                    )
                ).label("follows_user"),
            ]
        )
        .join(post_model.PostLike)
        .where(
            post_model.PostLike.post_id == post_id,
            post_model.PostLike.status == "ACT",
            post_model.PostLike.is_deleted == False,
            user_model.User.is_verified == True,
            user_model.User.is_deleted == False,
        )
    )
    if last_like_user_id:
        stmt = stmt.where(post_model.PostLike.user_id < last_like_user_id)

    stmt = stmt.order_by(post_model.PostLike.user_id.desc()).limit(limit)

    results = db_session.execute(stmt).fetchall()

    like_users_with_follow_status = [
        {
            "id": row[0],
            "profile_picture": row[1],
            "username": row[2],
            "follows_user": row[3] if curr_user_id != row[0] else None,
        }
        for row in results
    ]
    next_last_like_user_row = (
        like_users_with_follow_status[-1]["id"]
        if like_users_with_follow_status
        else None
    )

    return like_users_with_follow_status, next_last_like_user_row
