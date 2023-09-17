from pydantic import EmailStr

from app.config.base import BaseAppSettings


class EmailSettings(BaseAppSettings):
    email_host: str
    email_port: int
    email_username: str
    email_password: str
    email_from: EmailStr


email_settings = EmailSettings()
