from typing import Any

from pydantic.v1 import AnyHttpUrl, validator

from app.config.base import BaseAppSettings


class AppSettings(BaseAppSettings):
    """
    Necessary settings and params for app
    """

    docs_url: str | None = "/docs"
    openapi_url: str | None = "/openapi.json"
    redoc_url: str | None = "/redoc"
    title: str = "VPKonnect FastAPI application"
    version: str = "0.1.0"
    api_v0_prefix: str = "/api/v0"

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
