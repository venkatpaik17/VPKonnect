from typing import Literal

from pydantic import BaseModel, EmailStr, validator

from app.utils.exception import CustomValidationError


class UserLogin(BaseModel):
    username: EmailStr | str
    password: str
    device_info: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class AccessTokenPayload(BaseModel):
    email: EmailStr | None = None
    type: str | None = None


class RefreshTokenPayload(AccessTokenPayload):
    device_info: str | None = None
    token_id: str | None = None


class UserLogout(BaseModel):
    username: str
    device_info: str | None
    flow: Literal["user", "admin"]
    action: Literal["one", "all"]

    @validator("action")
    def check_action_flow(cls, val, values):
        flow_val = values["flow"]
        if flow_val == "admin" and val == "one":
            raise CustomValidationError(
                status_code=400,
                detail="Admin flow cannot have action as 'one'",
            )

        return val


class ResetTokenPayload(BaseModel):
    email: EmailStr | None = None
    token_id: str | None = None


class UserVerifyTokenPayload(ResetTokenPayload):
    pass


class EmployeeLogin(BaseModel):
    username: EmailStr | str
    password: str
    device_info: str


class EmployeeLogout(BaseModel):
    emp_id: str
    device_info: str
    action: Literal["one", "all"]
