from datetime import datetime
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


class CommentAdminResponse(BaseModel):
    id: UUID
    content: str
    status: str
    num_of_likes: int | None
    comment_user: CommentUserOutput
    posted_time_ago: str
    created_at: datetime
    is_ban_final: bool
    is_deleted: bool

    class Config:
        orm_mode = True
