from typing import Any
from uuid import UUID

from pydantic import BaseModel


class CommentBaseOutput(BaseModel):
    id: UUID


class CommentUserOutput(BaseModel):
    profile_picture: str
    username: str

    class Config:
        orm_mode = True


class CommentResponse(CommentBaseOutput):
    comment_user: CommentUserOutput
    content: str
    num_of_likes: int
    commented_time_ago: str
    curr_user_like: bool
    tag: str | None

    class Config:
        orm_mode = True


class LikeUserResponse(BaseModel):
    profile_picture: str
    username: str
    follows_user: bool | None

    class Config:
        orm_mode = True
