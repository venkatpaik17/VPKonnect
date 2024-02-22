from pydantic import BaseModel, EmailStr


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
    action: str
    flow: str


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
    action: str
