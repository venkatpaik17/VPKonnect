import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, validator

from app.utils.exception import CustomValidationError


class EmployeeBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    personal_email: EmailStr
    work_email: EmailStr
    join_date: date
    type: Literal["FTE", "PTE", "CTE"]
    designation: Literal[
        "CEO",
        "CTO",
        "CSO",
        "CMO",
        "CFO",
        "COO",
        "DHR",
        "DOP",
        "DOM",
        "HR1",
        "HR2",
        "HR3",
        "HRM1",
        "HRM2",
        "SDE1F",
        "SDE2F",
        "SDE3F",
        "SDE4F",
        "SDM1F",
        "SDM2F",
        "SDE1B",
        "SDE2B",
        "SDE3B",
        "SDE4B",
        "SDM1B",
        "SDM2B",
        "SDET1",
        "SDET2",
        "SDET3",
        "SDET4",
        "CCA",
        "CNM",
        "CMM",
        "UOA",
    ]
    supervisor: str | None


class EmployeeRegister(EmployeeBase):
    password: str = Field(min_length=8, max_length=48)
    confirm_password: str
    country_phone_code: str = Field(min_length=1, max_length=10)
    phone_number: str = Field(max_length=12)
    date_of_birth: date
    gender: Literal["M", "F", "N", "O"]
    aadhaar: str = Field(min_length=12, max_length=12)
    pan: str = Field(min_length=10, max_length=10)
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state_province: str
    zip_postal_code: str = Field(max_length=16)
    country: str = Field(min_length=3, max_length=3)

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
                raise CustomValidationError(
                    status_code=400,
                    detail="Invalid aadhaar number",
                )

        except ValueError as exc:
            raise CustomValidationError(
                status_code=400,
                detail="Invalid aadhaar number",
            ) from exc
        except IndexError as exc:
            raise CustomValidationError(
                status_code=400,
                detail="Invalid aadhaar number",
            ) from exc

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


class EmployeeRegisterResponse(EmployeeBase):
    emp_id: str
    profile_picture: str | None
    created_at: datetime

    class Config:
        orm_mode = True


class EmployeeOutput(BaseModel):
    emp_id: str
    first_name: str
    last_name: str


class SupervisorOutput(BaseModel):
    emp_id: str
    first_name: str
    last_name: str
    work_email: EmailStr
    designation: str

    class Config:
        orm_mode = True


class AllEmployeesAdminResponse(BaseModel):
    profile_picture: str | None
    emp_id: str
    first_name: str
    last_name: str
    personal_email: EmailStr
    work_email: EmailStr
    date_of_birth: date
    age: int
    gender: str
    join_date: date
    termination_date: date | None
    type: str
    designation: str
    supervisor: SupervisorOutput | None
    country_phone_code: str
    phone_number: str
    aadhaar: str
    pan: str
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state_province: str
    zip_postal_code: str
    country: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
