from logging import Logger
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import comment as comment_model
from app.schemas import auth as auth_schema
from app.schemas import comment as comment_schema
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import basic as basic_utils
from app.utils import log as log_utils

router = APIRouter(prefix=settings.api_prefix + "/comments", tags=["Comments"])

image_folder = settings.image_folder


# edit comment
@router.put("/{comment_id}")
@auth_utils.authorize(["user"])
def edit_comment(
    comment_id: UUID,
    content: str = Form(None),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    if curr_auth_user.status in ("RSF", "RSP"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit comment, user is under full restriction",
        )

    # get the comment
    comment = comment_service.get_a_comment(
        comment_id=str(comment_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # check if current user is permitted to edit the comment
    if comment.user_id != curr_auth_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform request operation",
        )

    if comment.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit banned comments",
        )
    elif comment.status == "FLB":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit flagged to be banned comments",
        )

    try:
        # update the comment
        comment.content = content
        comment.user_id = comment.user_id
        comment.post_id = comment.post_id

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error editing post",
        ) from exc

    # comment response
    comment_response = comment_schema.CommentResponse(
        id=comment.id,
        comment_user=comment.comment_user,
        content=content,
        num_of_likes=comment_service.count_comment_likes(
            comment_id=comment.id, status="ACT", db_session=db
        ),
        commented_time_ago=basic_utils.time_ago(comment.created_at),
        curr_user_like=comment_service.user_like_exists(
            user_id=comment.user_id, comment_id=comment.id, db_session=db
        )
        is not None,
        tag=None,
    )

    return {
        "message": "Comment has been edited successfully",
        "comment": comment_response,
    }


# remove comment
@router.delete("/{comment_id}")
@auth_utils.authorize(["user"])
def remove_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the post
    comment = comment_service.get_a_comment(
        comment_id=str(comment_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete banned comments",
        )

    # get post
    post = post_service.get_a_post(
        post_id=comment.post_id,
        status_not_in_list=["HID", "DRF", "BAN", "FLD", "FLB", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    # user is neither post owner nor comment onwer
    if (curr_auth_user.id != post.user_id) or (curr_auth_user.id != comment.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested operation",
        )

    # for RSF, post owner can delete other comments, comment owner cannot delete comment
    # both can delete FLB comment
    if curr_auth_user.status == "RSF" and comment.status != "FLB":
        if curr_auth_user.id != post.user_id or curr_auth_user.id == comment.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete comment.  is under full restriction",
            )

    # old comment status
    old_comment_status = comment.status

    try:
        # delete the comment
        comment.status = "FLD" if old_comment_status == "FLB" else "RMV"

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting comment",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"{old_comment_status} comment (id:{comment.id}) has been deleted successfully"
    }


# like a comment
@router.post("/{comment_id}/like")
@auth_utils.authorize(["user"])
def like_unlike_comment(
    comment_id: UUID,
    action: Literal["like", "unlike"] = Query(),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    if curr_auth_user.status in ("RSP", "RSF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} comment, user is under full/partial restriction",
        )

    # get the comment
    comment = comment_service.get_a_comment(
        comment_id=str(comment_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} banned comments",
        )
    elif comment.status == "FLB":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} flagged to be banned comments",
        )

    try:
        # check if you have already liked or not
        comment_like = comment_service.user_like_exists(
            user_id=curr_auth_user.id, comment_id=comment.id, db_session=db
        )

        # like a post, create a new entry
        if action == "like":
            if comment_like:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User has already liked the comment",
                )

            # add a like
            db.add(
                comment_model.CommentLike(
                    user_id=curr_auth_user.id, comment_id=comment.id
                )
            )

        # unlike a post, update the existing like entry
        elif action == "unlike":
            if not comment_like:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Like of user for the comment not found",
                )

            # update the like
            comment_like.status = "RMV"

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error {action}ing comment",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": f"Comment has been {action}d successfully"}


# get users who liked the comment
@router.get(
    "/{comment_id}/like",
    response_model=dict[str, list[comment_schema.LikeUserResponse] | UUID | str],
)
@auth_utils.authorize(["user"])
def get_comment_like_users(
    comment_id: UUID,
    limit: int = Query(3, le=9),
    last_like_user_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the comment
    comment = comment_service.get_a_comment(
        comment_id=str(comment_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.status in ("BAN", "FLB"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )

    # get the users
    like_users, next_cursor = comment_service.get_comment_like_users(
        curr_user_id=curr_auth_user.id,
        comment_id=comment.id,
        limit=limit,
        last_like_user_id=last_like_user_id,
        db_session=db,
    )

    if not like_users:
        if last_like_user_id:
            return {"message": "No more users who liked available", "info": "Done"}

        return {"message": "No users liked yet"}

    # like users response
    like_users_response = [
        comment_schema.LikeUserResponse(
            profile_picture=user["profile_picture"],
            username=user["username"],
            follows_user=user["follows_user"],
        )
        for user in like_users
    ]

    return {"like_users": like_users_response, "next_cursor": next_cursor}
