from enum import Enum

from pydantic import BaseSettings


class AppEnvTypes(str, Enum):
    """
    enum class for env types
    """

    PROD = "prod"
    DEV = "dev"
    TEST = "test"


class BaseAppSettings(BaseSettings):
    """
    base settings for app
    """

    app_environment: AppEnvTypes

    class Config:
        env_file = ".app.env"
        env_file_encoding = "utf-8"
