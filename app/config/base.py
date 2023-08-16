from enum import Enum

from pydantic.v1 import BaseSettings


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
        env_file = ".env"
        env_file_encoding = "utf-8"
