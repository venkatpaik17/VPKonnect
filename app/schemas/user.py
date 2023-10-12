import re
from datetime import date, datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, validator

from app.utils import enum as enum_utils


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    username: str = Field(min_length=1, max_length=30)
    email: EmailStr

    @validator("username", pre=True)
    def validate_username(cls, value):
        # Validation pattern for username
        pattern = r"^(?![.]+$)(?![_]+$)(?![\d]+$)(?![._]+$)(?!^[.])(?!.*\.{2,})[a-zA-Z0-9_.]{1,30}$"

        if not re.match(pattern, value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username"
            )

        # Convert username to lowercase
        return value.lower()


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=48)
    confirm_password: str
    date_of_birth: date
    gender: str
    country: str | None = None
    account_visibility: enum_utils.UserAccountVisibilityEnum | None
    bio: str | None = None


class UserRegisterResponse(UserBase):
    account_visibility: enum_utils.UserAccountVisibilityEnum
    profile_picture: str | None
    created_at: datetime

    class Config:
        orm_mode = True


class UserPasswordReset(BaseModel):
    email: EmailStr


class UserPasswordChangeReset(BaseModel):
    password: str = Field(min_length=8, max_length=48)
    confirm_password: str
    reset_token: str


class UserPasswordChangeUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=48)
    confirm_new_password: str


class UserFollowRequest(BaseModel):
    action: str


class UserFollow(UserFollowRequest):
    username: str


class UserUsernameChange(BaseModel):
    new_username: str = Field(min_length=1, max_length=30)


class UserFollowersFollowing(BaseModel):
    fetch: str


class UserGetFollowRequestsResponse(BaseModel):
    profile_picture: str | None
    username: str

    class Config:
        orm_mode = True


class UserFollowersFollowingResponse(UserGetFollowRequestsResponse):
    follows_user: bool | None


class UserDeletion(BaseModel):
    password: str
    hide_interactions: bool = False
