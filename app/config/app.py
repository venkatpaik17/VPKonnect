from pathlib import Path
from typing import Any

from pydantic import AnyHttpUrl, validator

from app.config.base import BaseAppSettings
from app.config.email import EmailSettings, email_settings


class AppSettings(BaseAppSettings):
    """
    Necessary settings and params for app
    """

    docs_url: str | None = "/docs"
    openapi_url: str | None = "/openapi.json"
    redoc_url: str | None = "/redoc"
    title: str = "VPKonnect FastAPI application"
    version: str = "0.1.0"
    api_prefix: str = "/api/v0"

    database_name: str
    database_username: str
    database_hostname: str
    database_port: str
    database_password: str

    access_token_secret_key: str
    refresh_token_secret_key: str
    token_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int

    email_settings: EmailSettings = email_settings
    reset_token_expire_minutes: int
    reset_token_secret_key: str
    user_verify_token_secret_key: str
    user_verify_token_expire_minutes: int
    image_max_size: int
    ttlcache_max_size: int
    image_folder: Path = Path("images")

    allowed_cors_origin: str | list[AnyHttpUrl]

    # validator for parsing list of cors origins
    @validator("allowed_cors_origin", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    # arguments for fastapi using property decorator
    @property
    def fastapi_kwargs(self) -> dict[str, Any]:
        return {
            "docs_url": self.docs_url,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
        }


settings = AppSettings()
