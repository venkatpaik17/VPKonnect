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
        invalid_username_message = """
            Invalid Username!!!
            Your username must meet the following criteria:
            - Must be between 1 and 30 characters long.
            - Can include letters (a-z, A-Z), digits (0-9), underscores (_), and periods (.).
            - Cannot contain consecutive periods (..).
            - Cannot start with a period (.).
            - Cannot consist solely of periods (.) or underscores (_), or digits only.
            - Cannot consist solely of periods and underscores.
            Examples of invalid usernames:
            - .... (consists only of periods)
            - ___ (consists only of underscores)
            - 12345 (consists only of digits)
            - ._._ (consists only of periods and underscores)
            - .username (starts with a period)
            - user..name (contains consecutive periods)
            Please update your username to meet these requirements.
        """

        message_lines = [
            line.strip() for line in invalid_username_message.strip().split("\n")
        ]

        if not re.match(pattern, value):
            raise CustomValidationError(status_code=400, detail=message_lines)

        # Convert username to lowercase
        return value.lower()


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=48)
    confirm_password: str
    date_of_birth: date
    gender: Literal["M", "F", "N", "O"]
    country: str | None
    account_visibility: Literal["PBC", "PRV"] | None
    bio: str | None = Field(None, max_length=150)
    country_phone_code: str | None = Field(None, min_length=1, max_length=10)
    phone_number: str | None = Field(None, max_length=12)

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

    @validator("password", pre=True)
    def validate_password(cls, value):
        pattern = (
            r"^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+={[}\]|:;\"'<,>.?/]).{8,48}$"
        )
        invalid_password_message = """
            Invalid Password!!!
            Your password must meet the following criteria:
            - At least 8 characters long (and no more than 48 characters).
            - Contains at least one uppercase letter (A-Z).
            - Contains at least one digit (0-9).
            - Contains at least one special character from the following set: `!@#$%^&*()_+-={}[]|:;\"'<,>.?/`.
            Examples of invalid passwords:
            - password (missing uppercase letter, digit, and special character)
            - P@ssword (missing digit)
            - 12345678 (missing uppercase letter and special character)
            - PASSWORD123 (missing special character)
            - password! (missing uppercase letter and digit)
            - Pass123 (too short, missing special character)
            - P@ss123456789012345678901234567890123456789012345 (too long, exceeds 48 characters)
            Please update your password to meet these requirements.
        """

        message_lines = [
            line.strip() for line in invalid_password_message.strip().split("\n")
        ]

        if not re.match(pattern, value):
            raise CustomValidationError(status_code=400, detail=message_lines)

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
    action: Literal["accept", "reject"]


class UserFollow(BaseModel):
    action: Literal["follow", "unfollow"]
    username: str


class UserUsernameChange(BaseModel):
    new_username: str = Field(min_length=1, max_length=30)

    @validator("new_username", pre=True)
    def validate_username(cls, value):
        # Validation pattern for username
        pattern = r"^(?![.]+$)(?![_]+$)(?![\d]+$)(?![._]+$)(?!^[.])(?!.*\.{2,})[a-zA-Z0-9_.]{1,30}$"

        invalid_username_message = """
            Invalid Username!!!
            Your username must meet the following criteria:
            - Must be between 1 and 30 characters long.
            - Can include letters (a-z, A-Z), digits (0-9), underscores (_), and periods (.).
            - Cannot contain consecutive periods (..).
            - Cannot start with a period (.).
            - Cannot consist solely of periods (.) or underscores (_), or digits only.
            - Cannot consist solely of periods and underscores.
            Examples of invalid usernames:
            - .... (consists only of periods)
            - ___ (consists only of underscores)
            - 12345 (consists only of digits)
            - ._._ (consists only of periods and underscores)
            - .username (starts with a period)
            - user..name (contains consecutive periods)
            Please update your username to meet these requirements.
        """

        message_lines = [
            line.strip() for line in invalid_username_message.strip().split("\n")
        ]

        if not re.match(pattern, value):
            raise CustomValidationError(status_code=400, detail=message_lines)

        # Convert username to lowercase
        return value.lower()


# class UserFollowersFollowing(BaseModel):
#     fetch: str


class UserGetFollowRequestsResponse(BaseModel):
    profile_picture: str | None
    username: str

    class Config:
        orm_mode = True


class UserFollowersFollowingResponse(UserGetFollowRequestsResponse):
    follows_user: bool | None


# class UserRemoveFollower(BaseModel):
#     username: str


class UserDeactivationDeletion(BaseModel):
    password: str


class UserSendVerifyEmail(BaseModel):
    email: EmailStr
    type: str


class UserContentReport(BaseModel):
    username: str
    item_type: Literal["post", "comment", "account"]
    item_id: UUID | None
    reason: str
    reason_username: str | None

    @validator("item_id")
    def validate_item_id(cls, val, values):
        item_type_val = values["item_type"]
        # if post/comment doesn't have item_id or account have item_id
        if (item_type_val in ("post", "comment") and not val) or (
            item_type_val == "account" and val
        ):
            if item_type_val in ("post", "comment"):
                raise CustomValidationError(
                    status_code=400,
                    detail="Item ID is required for posts and comments.",
                )
            else:
                raise CustomValidationError(
                    status_code=400,
                    detail="Item ID should not be provided for accounts.",
                )

        return val


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
    content_type: Literal["post", "comment", "account"]
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
    bio: str | None
    followed_by: list[str] | None
    follows_user: bool | None

    class Config:
        orm_mode = True


# class UserPostRequest(BaseModel):
#     post_status: Literal["PUB", "DRF", "BAN", "FLB"]


class UserFeedResponse(BaseModel):
    posts: list[PostUserFeedResponse]
    next_cursor: UUID | None

    class Config:
        orm_mode = True


# class AllUsersAdminRequest(BaseModel):
#     status: list[str] | None = None
#     sort: str | None = None


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


class UserAdminResponse(AllUsersAdminResponse):
    num_of_posts: int
    num_of_followers: int
    num_of_following: int


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


class UserAboutResponse(BaseModel):
    profile_picture: str | None
    username: str
    account_created_on: date
    account_based_in: str | None
    num_of_former_usernames: int | None = None
    former_usernames: list[str] | None = None

    class Config:
        orm_mode = True
