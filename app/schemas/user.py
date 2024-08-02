import re
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import UUID4, BaseModel, EmailStr, Field, validator

from app.schemas.post import PostUserFeedResponse
from app.utils.exception import CustomValidationError


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
            raise CustomValidationError(
                status_code=400, detail=f"Invalid username: {value}"
            )

        # Convert username to lowercase
        return value.lower()


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=48)
    confirm_password: str
    date_of_birth: date
    gender: str
    country: str | None
    account_visibility: str | None
    bio: str | None
    country_phone_code: str = Field(min_length=1, max_length=10)
    phone_number: str = Field(max_length=12)

    @validator("date_of_birth", pre=True)
    def validate_age_from_date_of_birth(cls, value):
        # get current date
        current_date = datetime.now().date()

        # get the age
        age = (
            current_date.year
            - value.year
            - ((current_date.month, current_date.day) < (value.month, value.day))
        )

        # check the age
        if age < 16:
            raise CustomValidationError(
                status_code=400,
                detail="User must be of age 16 or above",
            )

        return value


class UserRegisterResponse(UserBase):
    repr_id: UUID4
    account_visibility: str
    profile_picture: str | None
    created_at: datetime

    class Config:
        orm_mode = True


class UserVerifyResponse(BaseModel):
    message: str
    data: UserRegisterResponse


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

    @validator("new_username", pre=True)
    def validate_username(cls, value):
        # Validation pattern for username
        pattern = r"^(?![.]+$)(?![_]+$)(?![\d]+$)(?![._]+$)(?!^[.])(?!.*\.{2,})[a-zA-Z0-9_.]{1,30}$"

        if not re.match(pattern, value):
            raise CustomValidationError(
                status_code=400, detail=f"Invalid username: {value}"
            )

        # Convert username to lowercase
        return value.lower()


class UserFollowersFollowing(BaseModel):
    fetch: str


class UserGetFollowRequestsResponse(BaseModel):
    profile_picture: str | None
    username: str

    class Config:
        orm_mode = True


class UserFollowersFollowingResponse(UserGetFollowRequestsResponse):
    follows_user: bool | None


class UserRemoveFollower(BaseModel):
    username: str


class UserDeactivationDeletion(BaseModel):
    password: str


class UserSendVerifyEmail(BaseModel):
    email: EmailStr
    type: str


class UserContentReport(BaseModel):
    username: str
    item_id: UUID | None
    item_type: str
    reason: str
    reason_username: str | None


class UserBaseOutput(BaseModel):
    username: str

    class Config:
        orm_mode = True


class UserPostOutput(UserBaseOutput):
    profile_image: str | None


class UserOutput(UserBaseOutput):
    status: str
    email: EmailStr


class UserContentAppeal(BaseModel):
    username: str
    email: EmailStr
    content_type: str
    content_id: UUID | None
    detail: str

    @validator("content_id")
    def validate_content_id(cls, val, values):
        content_type_val = values["content_type"]
        # if post/comment doesn't have content_id or account have content_id
        if (content_type_val in ("post", "comment") and not val) or (
            content_type_val == "account" and val
        ):
            if content_type_val in ("post", "comment"):
                raise CustomValidationError(
                    status_code=400,
                    detail="Content ID is required for posts and comments.",
                )
            else:
                raise CustomValidationError(
                    status_code=400,
                    detail="Content ID should not be provided for accounts.",
                )

        return val


class UserProfileResponse(UserBaseOutput):
    profile_picture: str | None
    num_of_posts: int
    num_of_followers: int
    num_of_following: int
    followed_by: list[str] | None
    follows_user: bool | None

    class Config:
        orm_mode = True


class UserPostRequest(BaseModel):
    post_status: Literal["PUB", "DRF", "BAN", "FLB"]


class UserFeedResponse(BaseModel):
    posts: list[PostUserFeedResponse]
    next_cursor: UUID | None

    class Config:
        orm_mode = True


class AllUsersAdminRequest(BaseModel):
    status: list[str] | None = None
    sort: str | None = None


class AllUsersAdminResponse(BaseModel):
    profile_picture: str | None
    repr_id: UUID4
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    country_phone_code: str | None
    phone_number: str | None
    date_of_birth: date
    age: int
    gender: str
    country: str | None
    account_visibility: str
    bio: str | None
    status: str
    type: str
    inactive_delete_after: int
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True


class UserActiveRestrictBan(BaseModel):
    status: str
    duration: str
    enforce_action_at: datetime


class UserViolationDetailResponse(BaseModel):
    num_of_post_violations_no_restrict_ban: int
    num_of_comment_violations_no_restrict_ban: int
    num_of_account_violations_no_restrict_ban: int
    total_num_of_violations_no_restrict_ban: int
    num_of_partial_account_restrictions: int
    num_of_full_account_restrictions: int
    num_of_account_temporary_bans: int
    num_of_account_permanent_bans: int
    total_num_of_account_restrict_bans: int
    active_restrict_ban: UserActiveRestrictBan | None
    violation_score: int

    class Config:
        orm_mode = True
