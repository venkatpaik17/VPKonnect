from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, validator

from app.utils.exception import CustomValidationError


class PostCreate(BaseModel):
    post_type: Literal["PUB", "DRF"]
    caption: str | None

    @validator("post_type", pre=True)
    def transform_post_type(cls, value):
        if value == "publish":
            return "PUB"
        elif value == "draft":
            return "DRF"
        raise CustomValidationError(
            status_code=400, detail=f"Invalid status value: {value}"
        )


class PostOutput(BaseModel):
    id: UUID


class PostUserOutput(BaseModel):
    profile_picture: str
    username: str

    class Config:
        orm_mode = True


class PostDraftResponse(PostOutput):
    status: str
    image: str
    caption: str | None


class PostProfileResponse(PostOutput):
    image: str
    num_of_likes: int | None
    num_of_comments: int | None

    class Config:
        orm_mode = True


class PostUserFeedResponse(PostProfileResponse):
    post_user: PostUserOutput
    caption: str | None
    posted_time_ago: str
    curr_user_like: bool

    class Config:
        orm_mode = True


class PostResponse(PostUserFeedResponse):
    date: date
    tag: str | None  # for FLB

    class Config:
        orm_mode = True


class EditPostRequest(BaseModel):
    id: UUID
    post_type: Literal["published", "draft"]
    action: Literal["publish", "edit"]
    caption: str | None

    @validator("action")
    def check_post_type_action(cls, val, values):
        post_type_val = values.get("post_type")
        if post_type_val == "published" and val == "publish":
            raise CustomValidationError(
                status_code=400,
                detail="Invalid request. Cannot publish an already published post",
            )

        return val


class LikeUserResponse(BaseModel):
    profile_picture: str
    username: str
    follows_user: bool | None
