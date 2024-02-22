from datetime import date, datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, validator


class EmployeeBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    personal_email: EmailStr
    work_email: EmailStr
    join_date: date
    type: str
    designation: str


class EmployeeRegister(EmployeeBase):
    password: str = Field(min_length=8, max_length=48)
    confirm_password: str
    country_phone_code: str = Field(min_length=1, max_length=10)
    phone_number: str = Field(max_length=12)
    date_of_birth: date
    gender: str
    aadhaar: str = Field(min_length=12, max_length=12)
    pan: str = Field(min_length=10, max_length=10)
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state_province: str
    zip_postal_code: str = Field(max_length=16)
    country: str

    @validator("aadhaar", pre=True)
    def validate_aadhaar(cls, value):
        # verhoeff algorithm
        mult = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
        ]
        perm = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
        ]

        try:
            i = len(value)
            j = 0
            x = 0

            while i > 0:
                i -= 1
                x = mult[x][perm[(j % 8)][int(value[i])]]
                j += 1
            if x == 0:
                return value
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid aadhaar number",
                )

        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid aadhaar number",
            ) from exc
        except IndexError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid aadhaar number",
            ) from exc


class EmployeeRegisterResponse(EmployeeBase):
    emp_id: str
    profile_picture: str | None
    created_at: datetime

    class Config:
        orm_mode = True


class EmployeeOutput(BaseModel):
    emp_id: str
