from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    username: EmailStr | str
    password: str
    device_info: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str
