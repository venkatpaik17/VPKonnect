from logging import Logger
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config.app import settings
from app.db.session import get_db
from app.models import comment as comment_model
from app.models import post as post_model
from app.schemas import auth as auth_schema
from app.schemas import comment as comment_schema
from app.schemas import post as post_schema
from app.services import comment as comment_service
from app.services import post as post_service
from app.services import user as user_service
from app.utils import auth as auth_utils
from app.utils import basic as basic_utils
from app.utils import image as image_utils
from app.utils import log as log_utils

router = APIRouter(prefix=settings.api_prefix + "/posts", tags=["Posts"])

image_folder = settings.image_folder


# create post
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
@auth_utils.authorize(["user"])
def create_post(
    image: UploadFile,
    post_type: Literal["publish", "draft"] = Query(),
    caption=Form(None),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # request schema
    post_request = post_schema.PostCreate(post_type=post_type, caption=caption)

    # get the current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # RSF cannot post
    if curr_auth_user.status == "RSF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create new post, user is under full restriction",
        )

    image_path = None
    try:
        # image validation and handling
        image_name = image_utils.validate_image_generate_name(
            username=curr_auth_user.username,
            image=image,
            logger=logger,
        )

        # posts folder
        posts_subfolder = image_folder / "user" / str(curr_auth_user.repr_id) / "posts"

        image_path = posts_subfolder / image_name

        # write image to target folder
        image_utils.write_image(
            image=image,
            image_path=image_path,
            logger=logger,
        )

        new_post = post_model.Post(
            status=post_request.post_type,
            caption=post_request.caption,
            image=image_name,
            user_id=curr_auth_user.id,
        )

        db.add(new_post)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating post",
        ) from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    db.refresh(new_post)

    if post_request.post_type == "DRF":
        new_post_response = post_schema.PostDraftResponse(id=new_post.id, status=new_post.status, image=new_post.image, caption=new_post.caption)  # type: ignore
        message = "Post created has been saved as draft successfully"

    else:
        new_post_response = post_schema.PostUserFeedResponse(
            id=new_post.id,
            image=new_post.image,
            num_of_likes=post_service.count_post_likes(
                post_id=new_post.id, status="ACT", db_session=db
            ),
            num_of_comments=comment_service.count_comments(
                post_id=new_post.id, status_in_list=["PUB", "FLB"], db_session=db
            ),
            post_user=new_post.post_user,
            caption=new_post.caption,
            posted_time_ago=basic_utils.time_ago(post_datetime=new_post.created_at),
            curr_user_like=post_service.user_like_exists(
                user_id=curr_auth_user.id, post_id=new_post.id, db_session=db
            )
            is not None,
        )
        message = "New post has been created successfully"

    return {"message": message, "post": new_post_response}


# get a post
@router.get("/{post_id}")
@auth_utils.authorize(["user"])
def get_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get the current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the post
    post = post_service.get_a_post(
        post_id=str(post_id), status_not_in_list=["HID", "FLD", "RMV"], db_session=db
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested post not found or might be deleted",
        )

    # get the post owner
    post_user = user_service.get_user_by_id(
        user_id=post.user_id,
        status_not_in_list=None,
        db_session=db,
    )
    if not post_user:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post owner not found"
        )

    # redirect to user profile if user is deactivated or deleted
    if post_user.status in ("DAH", "PDH", "PBN", "PDB", "PDI", "DEL"):
        return RedirectResponse(
            settings.api_prefix + "/users/" + str(post_user.username) + "/profile",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # check whether current user follows post_user or not
    follower_check = user_service.check_user_follower_or_not(
        follower_id=str(curr_auth_user.id), followed_id=str(post_user.id), db_session=db
    )

    flagged = False
    tag = None
    if post_user.username != curr_auth_user.username:
        # if post user is private and curr user is not a follower then redirect to user profile
        if post_user.account_visibility == "PRV" and not follower_check:
            return RedirectResponse(
                settings.api_prefix + "/users/" + str(post_user.username) + "/profile",
                status_code=status.HTTP_303_SEE_OTHER,
            )
        elif post.status == "BAN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Requested post is banned"
            )
        elif post.status == "FLB":
            flagged = True
            tag = "flagged to be banned"
        elif post.status == "DRF":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access requested resource",
            )

    # post response
    if post.status == "DRF":
        post_response = post_schema.PostDraftResponse(
            id=post.id, status=post.status, image=post.image, caption=post.caption
        )
    else:
        post_response = post_schema.PostResponse(
            id=post.id,
            image=post.image,
            num_of_likes=post_service.count_post_likes(
                post_id=post.id, status="ACT", db_session=db
            ),
            num_of_comments=comment_service.count_comments(
                post_id=post.id, status_in_list=["PUB", "FLB"], db_session=db
            ),
            post_user=post.post_user,
            caption=post.caption,
            posted_time_ago=basic_utils.time_ago(post_datetime=post.created_at),
            curr_user_like=(
                post_service.user_like_exists(
                    user_id=curr_auth_user.id, post_id=post.id, db_session=db
                )
                is not None
                and not flagged
            ),
            date=post.created_at,
            tag=tag,
        )

    return post_response


# edit post
# published post -> edit; caption only
# draft post -> publish, edit; image and caption
@router.put("/{post_id}")
@auth_utils.authorize(["user"])
def edit_post(
    post_id: UUID,
    post_type: Literal["published", "draft"] = Query(),
    action: Literal["edit", "publish"] = Query(),
    caption: str = Form(None),
    image: UploadFile | None = None,
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # request
    edit_request = post_schema.EditPostRequest(
        id=post_id, post_type=post_type, action=action, caption=caption
    )

    # get current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    if curr_auth_user.status == "RSF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit post, user is under full restriction",
        )

    # get the post
    post = post_service.get_a_post(
        post_id=str(edit_request.id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # check if current user is permitted to edit the post
    if post.user_id != curr_auth_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform request operation",
        )

    if post.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit banned posts",
        )
    elif post.status == "FLB":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit flagged to be banned posts",
        )

    if post.status == "PUB":
        if edit_request.post_type == "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Post type mismatch. Post to be edited is a published post, not a draft post",
            )
        if image:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request. Cannot replace image in published post",
            )

    elif post.status == "DRF" and edit_request.post_type == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post type mismatch. Post to be {edit_request.action}ed is a draft post, not a published post",
        )

    posts_subfolder = None
    old_image = post.image
    image_path = None

    try:
        if image:
            # image validation and name generation
            image_name = image_utils.validate_image_generate_name(
                username=curr_auth_user.username,
                image=image,
                logger=logger,
            )

            # posts folder
            posts_subfolder = (
                image_folder / "user" / str(curr_auth_user.repr_id) / "posts"
            )

            image_path = posts_subfolder / image_name

            # write image
            image_utils.write_image(
                image=image,
                image_path=image_path,
                logger=logger,
            )

        else:
            image_name = old_image

        # update the post
        # draft publish, since published post cannot be published, handled in schema validator
        if edit_request.action == "publish":
            post.status = "PUB"
            post.caption = edit_request.caption
            post.image = image_name

        elif edit_request.action == "edit":
            if edit_request.post_type == "published":
                post.status = "PUB"
                post.caption = edit_request.caption
                post.image = image_name

            elif edit_request.post_type == "draft":
                post.status = "DRF"
                post.caption = edit_request.caption
                post.image = image_name

        post.user_id = post.user_id

        db.commit()

        if image:
            # if draft has updated image and everything is completed without error, delete old image of draft
            remove_path = posts_subfolder / old_image
            image_utils.remove_image(path=remove_path)
            logger.info("Old draft image removed, path: %s", remove_path)

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if image and image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error editing post",
        ) from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        if image and image_path:
            image_utils.remove_image(path=image_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    if edit_request.post_type == "draft" and edit_request.action == "edit":
        edit_post_response = post_schema.PostDraftResponse(
            id=post.id, status=post.status, image=post.image, caption=post.caption
        )
        message = "Draft has been edited and saved successfully"

    else:
        edit_post_response = post_schema.PostResponse(
            id=post.id,
            image=post.image,
            num_of_likes=post_service.count_post_likes(
                post_id=post.id, status="ACT", db_session=db
            ),
            num_of_comments=comment_service.count_comments(
                post_id=post.id, status_in_list=["PUB", "FLB"], db_session=db
            ),
            post_user=post.post_user,
            caption=post.caption,
            posted_time_ago=basic_utils.time_ago(post_datetime=post.created_at),
            curr_user_like=post_service.user_like_exists(
                user_id=curr_auth_user.id, post_id=post.id, db_session=db
            )
            is not None,
            date=post.created_at,
            tag=None,
        )
        if edit_request.action == "publish":
            message = "Draft post has been published succesfully"
        else:
            message = "Post has been edited successfully"

    return {"message": message, "post": edit_post_response}


# remove post
@router.delete("/{post_id}")
@auth_utils.authorize(["user"])
def remove_post(
    post_id: UUID,
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
    post = post_service.get_a_post(
        post_id=str(post_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete banned posts"
        )

    if curr_auth_user.status == "RSF":
        # can only delete FLB in RSF
        if post.status != "FLB":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete post, user is under full restriction",
            )

    # check if current user is permitted to delete the post
    if post.user_id != curr_auth_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform request operation",
        )

    # old post status
    old_post_status = post.status

    try:
        # delete the post
        post.status = "FLD" if old_post_status == "FLB" else "RMV"

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting post",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {
        "message": f"{old_post_status} post (id:{post.id}) has been deleted successfully"
    }


# like unlike post
@router.post("/{post_id}/like")
@auth_utils.authorize(["user"])
def like_unlike_post(
    post_id: UUID,
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
            detail=f"Cannot {action} post, user is under full/partial restriction",
        )

    # get the post
    post = post_service.get_a_post(
        post_id=str(post_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} banned posts",
        )
    elif post.status == "FLB":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} flagged to be banned posts",
        )
    elif post.status == "DRF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} flagged to be banned posts",
        )

    try:
        # check if you have already like or not
        post_like = post_service.user_like_exists(
            user_id=curr_auth_user.id, post_id=post.id, db_session=db
        )
        # like a post, create a new entry
        if action == "like":
            if post_like:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User has already liked the post",
                )

            # add a like
            db.add(post_model.PostLike(user_id=curr_auth_user.id, post_id=post.id))

        # unlike a post, update the existing like entry
        elif action == "unlike":
            if not post_like:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Like of user for the post not found",
                )

            # update the like
            post_like.status = "RMV"

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error {action}ing post",
        ) from exc
    except HTTPException as exc:
        db.rollback()
        raise exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return {"message": f"Post has been {action}d successfully"}


# get users who liked the post
@router.get(
    "/{post_id}/like",
    response_model=dict[str, list[post_schema.LikeUserResponse] | UUID | str],
)
@auth_utils.authorize(["user"])
def get_post_like_users(
    post_id: UUID,
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

    # get the post
    post = post_service.get_a_post(
        post_id=str(post_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.status in ("BAN", "DRF", "FLB"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )

    # get the users
    like_users, next_cursor = post_service.get_post_like_users(
        curr_user_id=curr_auth_user.id,
        post_id=post.id,
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
        post_schema.LikeUserResponse(
            profile_picture=user["profile_picture"],
            username=user["username"],
            follows_user=user["follows_user"],
        )
        for user in like_users
    ]

    return {"like_users": like_users_response, "next_cursor": next_cursor}


# comment on post
@router.post("/{post_id}/comments", status_code=status.HTTP_201_CREATED)
@auth_utils.authorize(["user"])
def create_comment(
    post_id: UUID,
    content=Form(None),
    db: Session = Depends(get_db),
    logger: Logger = Depends(log_utils.get_logger),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get the current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    if curr_auth_user.status in ("RSP", "RSF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot comment, user is under full/partial restriction",
        )

    # get the post
    post = post_service.get_a_post(
        post_id=str(post_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    if post.status == "DRF":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot comment on draft posts",
        )
    if post.status == "BAN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot comment on banned posts",
        )
    elif post.status == "FLB":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot comment on flagged to be banned posts",
        )

    try:
        new_comment = comment_model.Comment(
            content=content, user_id=curr_auth_user.id, post_id=post.id
        )

        db.add(new_comment)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating comment",
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.error(exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    db.refresh(new_comment)

    # comment response
    comment_response = comment_schema.CommentResponse(
        id=new_comment.id,
        comment_user=new_comment.comment_user,
        content=content,
        num_of_likes=comment_service.count_comment_likes(
            comment_id=new_comment.id, status="ACT", db_session=db
        ),
        commented_time_ago=basic_utils.time_ago(new_comment.created_at),
        curr_user_like=comment_service.user_like_exists(
            user_id=new_comment.user_id, comment_id=new_comment.id, db_session=db
        )
        is not None,
        tag=None,
    )

    return {
        "message": f"Comment added to post (id:{post.id})",
        "comment": comment_response,
    }


# get post comments
@router.get(
    "/{post_id}/comments",
    response_model=dict[str, list[comment_schema.CommentResponse] | UUID | str],
)
@auth_utils.authorize(["user"])
def get_all_comments(
    post_id: UUID,
    limit: int = Query(3, le=9),
    last_comment_id: UUID = Query(None),
    db: Session = Depends(get_db),
    current_user: auth_schema.AccessTokenPayload = Depends(auth_utils.get_current_user),
):
    # get the current user
    curr_auth_user = user_service.get_user_by_email(
        email=str(current_user.email),
        status_not_in_list=["INA", "DAH", "PDH", "TBN", "PBN", "PDB", "PDI", "DEL"],
        db_session=db,
    )

    # get the post
    post = post_service.get_a_post(
        post_id=str(post_id),
        status_not_in_list=["HID", "FLD", "RMV"],
        db_session=db,
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    if post.status in ("DRF", "BAN", "FLB"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request. Cannot get comments",
        )

    # get all comments
    all_comments, next_cursor = comment_service.get_all_comments_of_post(
        post_id=post_id,
        status_in_list=["PUB", "FLB"],
        limit=limit,
        last_comment_id=last_comment_id,
        db_session=db,
    )
    if not all_comments:
        if last_comment_id:
            return {"message": "No more comments available", "info": "Done"}

        return {"message": "No comments yet"}

    # get all comment ids
    all_comments_ids = [comment.id for comment in all_comments]

    # get likes of all comments
    likes_comments = comment_service.count_all_comments_likes(
        comment_id_list=all_comments_ids, db_session=db
    )

    # curr user comments like, all the comments liked by curr user
    curr_user_comments_like = comment_service.curr_user_like_for_exists_comments(
        comment_id_list=all_comments_ids, curr_user_id=curr_auth_user.id, db_session=db
    )

    # comments response
    all_comments_response = [
        comment_schema.CommentResponse(
            id=comment.id,
            comment_user=comment.comment_user,
            content=comment.content,
            num_of_likes=likes_comments.get(comment.id, 0),
            commented_time_ago=basic_utils.time_ago(comment.created_at),
            curr_user_like=comment.id in curr_user_comments_like,
            tag="flagged to be banned" if comment.status == "FLB" else None,
        )
        for comment in all_comments
    ]

    return {"comments": all_comments_response, "next_cursor": next_cursor}
