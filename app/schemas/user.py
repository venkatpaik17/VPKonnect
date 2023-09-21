from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    username: str = Field(min_length=1, max_length=30)
    email: EmailStr


class UserRegister(UserBase):
    password: str = Field(min_length=8, max_length=48)
    date_of_birth: date
    gender: str
    country: str | None = None


class UserRegisterResponse(UserBase):
    profile_picture: str | None
    created_at: datetime

    class Config:
        orm_mode = True


class UserPasswordReset(BaseModel):
    email: EmailStr


class UserPasswordChangeReset(BaseModel):
    password: str
    confirm_password: str
    reset_token: str


class UserPasswordChangeUpdate(BaseModel):
    old_password: str
    new_password: str
    confirm_new_password: str


class UserFollowRequest(BaseModel):
    action: str


class UserFollow(UserFollowRequest):
    username: str
