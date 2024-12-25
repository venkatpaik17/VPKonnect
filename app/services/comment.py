from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.models import comment as comment_model
from app.models import user as user_model


def get_a_comment_query(
    comment_id: str, status_not_in_list: list[str] | None, db_session: Session
):
    return db_session.query(comment_model.Comment).filter(
        comment_model.Comment.id == comment_id,
        (
            comment_model.Comment.status.notin_(status_not_in_list)
            if status_not_in_list
            else True
        ),
        comment_model.Comment.is_deleted == False,
        comment_model.Comment.is_ban_final == False,
    )


def get_a_comment(
    comment_id: str, status_not_in_list: list[str] | None, db_session: Session
):
    return get_a_comment_query(comment_id, status_not_in_list, db_session).first()


def get_all_comments_by_id_query(
    comment_id_list: list[UUID], status_in_list: list[str], db_session: Session
):
    return db_session.query(comment_model.Comment).filter(
        comment_model.Comment.id.in_(comment_id_list),
        comment_model.Comment.status.in_(status_in_list),
        comment_model.Comment.is_deleted == False,
        comment_model.Comment.is_ban_final == False,
    )


def count_comments(post_id: UUID, status_in_list: list[str], db_session: Session):
    return (
        db_session.query(func.count(comment_model.Comment.id))
        .filter(
            comment_model.Comment.post_id == post_id,
            comment_model.Comment.status.in_(status_in_list),
            comment_model.Comment.is_deleted == False,
            comment_model.Comment.is_ban_final == False,
        )
        .scalar()
    )


def count_comments_admin(
    post_id: UUID, status_in_list: list[str] | None, db_session: Session
):
    return (
        db_session.query(func.count(comment_model.Comment.id))
        .filter(
            comment_model.Comment.post_id == post_id,
            (
                comment_model.Comment.status.in_(status_in_list)
                if status_in_list
                else True
            ),
        )
        .scalar()
    )


def get_all_comments_of_post(
    post_id: UUID,
    status_in_list: list[str] | None,
    limit: int,
    last_comment_id: UUID | None,
    db_session: Session,
    is_ban_final: bool = False,
):
    query = db_session.query(comment_model.Comment).filter(
        comment_model.Comment.post_id == post_id,
        comment_model.Comment.status.in_(status_in_list) if status_in_list else True,
        comment_model.Comment.is_ban_final == is_ban_final,
        comment_model.Comment.is_deleted == False,
    )

    if last_comment_id:
        query = query.filter(comment_model.Comment.id < last_comment_id)

    results = query.order_by(comment_model.Comment.id.desc()).limit(limit).all()
    next_last_comment_id = results[-1].id if results else None

    return results, next_last_comment_id


def count_comment_likes(comment_id: UUID, status: str, db_session: Session):
    return (
        db_session.query(func.count(comment_model.CommentLike.id))
        .filter(
            comment_model.CommentLike.comment_id == comment_id,
            comment_model.CommentLike.status == status,
            comment_model.CommentLike.is_deleted == False,
        )
        .scalar()
    )


def count_comment_likes_admin(
    comment_id: UUID, status_in_list: list[str], db_session: Session
):
    return (
        db_session.query(func.count(comment_model.CommentLike.id))
        .filter(
            comment_model.CommentLike.comment_id == comment_id,
            comment_model.CommentLike.status.in_(status_in_list),
            comment_model.CommentLike.is_deleted == False,
        )
        .scalar()
    )


def count_all_comments_likes(comment_id_list: list[UUID], db_session: Session):
    results = (
        db_session.query(
            comment_model.CommentLike.comment_id,
            func.count(comment_model.CommentLike.id),
        )
        .filter(
            comment_model.CommentLike.comment_id.in_(comment_id_list),
            comment_model.CommentLike.status == "ACT",
            comment_model.CommentLike.is_deleted == False,
        )
        .group_by(comment_model.CommentLike.comment_id)
        .all()
    )

    # return defaultdict(int, results)
    return dict(results)


def user_like_exists(user_id: UUID, comment_id: UUID, db_session: Session):
    return (
        db_session.query(comment_model.CommentLike)
        .filter(
            comment_model.CommentLike.user_id == user_id,
            comment_model.CommentLike.comment_id == comment_id,
            comment_model.CommentLike.status == "ACT",
            comment_model.CommentLike.is_deleted == False,
        )
        .first()
    )


def curr_user_like_for_exists_comments(
    comment_id_list: list[UUID], curr_user_id: UUID, db_session: Session
):
    stmt = select(comment_model.CommentLike.comment_id).filter(
        comment_model.CommentLike.comment_id.in_(comment_id_list),
        comment_model.CommentLike.status == "ACT",
        comment_model.CommentLike.user_id == curr_user_id,
        comment_model.CommentLike.is_deleted == False,
    )

    return db_session.execute(stmt).scalars().all()


def get_comment_like_users(
    curr_user_id: UUID,
    comment_id: UUID,
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
        .join(comment_model.CommentLike)
        .where(
            comment_model.CommentLike.comment_id == comment_id,
            comment_model.CommentLike.status == "ACT",
            comment_model.CommentLike.is_deleted == False,
            user_model.User.is_verified == True,
            user_model.User.is_deleted == False,
        )
    )
    if last_like_user_id:
        stmt = stmt.where(comment_model.CommentLike.user_id < last_like_user_id)

    stmt = stmt.order_by(comment_model.CommentLike.user_id.desc()).limit(limit)

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


def get_a_comment_admin(
    comment_id: str, status_not_in_list: list[str] | None, db_session: Session
):
    return (
        db_session.query(comment_model.Comment)
        .filter(
            comment_model.Comment.id == comment_id,
            (
                comment_model.Comment.status.notin_(status_not_in_list)
                if status_not_in_list
                else True
            ),
        )
        .first()
    )
