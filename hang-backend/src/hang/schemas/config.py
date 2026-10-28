from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
from typing_extensions import Annotated


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 5

    REDIS_HOST: str
    REDIS_PORT: int = 6379
    RATE_LIMIT_STORAGE_URI: str = ""

    COOKIE_SECURE: bool = False

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    MAX_IMAGES: int
    MAX_IMAGE_SIZE: int
    ALLOWED_IMAGE_TYPES: Annotated[str, "csv"]

    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_ENDPOINT: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    @field_validator("ALLOWED_IMAGE_TYPES", mode="after")
    @classmethod
    def split_allowed_image_types(cls, v: str) -> List[str]:
        return [x.strip() for x in v.split(",") if x.strip()]

    model_config = SettingsConfigDict(env_file=".api.env", env_file_encoding="utf-8")


conf = Settings()
