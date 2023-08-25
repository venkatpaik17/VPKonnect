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
