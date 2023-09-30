from typing import Any

from pydantic import BaseModel, EmailStr


class SendEmail(BaseModel):
    template: str
    email: list[EmailStr]
    body_info: dict[str, Any]
