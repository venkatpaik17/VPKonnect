import re
from datetime import date, datetime
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import UUID4, BaseModel, EmailStr, Field, validator


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
    account_visibility: str | None
    bio: str | None = None

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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
    hide_interactions: bool = False


class UserSendEmail(BaseModel):
    email: EmailStr
    type: str


class UserContentReport(BaseModel):
    username: str
    item_id: UUID | None
    item_type: str
    reason: str
    reason_username: str | None


class UserOutput(BaseModel):
    username: str


class UserContentAppeal(BaseModel):
    username: str
    email: EmailStr
    content_type: str
    content_id: UUID | None
    user_status: str | None
    detail: str
