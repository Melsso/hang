from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Dict
from typing_extensions import Annotated
from pathlib import Path
import pycountry


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5432

    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    MAX_IMAGES: int
    MAX_IMAGE_SIZE: int
    ALLOWED_IMAGE_TYPES: Annotated[str, "csv"]

    STATIC_DIRECTORY: Path

    R2_ACCESS_KEY_ID: str
    R2_SECRET_ACCESS_KEY: str
    R2_BUCKET_NAME: str
    R2_ENDPOINT: str

    COUNTRIES: List[Dict[str, str]] = [
        {"code": c.alpha_2, "name": c.name} for c in pycountry.countries
    ]

    @field_validator("ALLOWED_IMAGE_TYPES", mode="after")
    @classmethod
    def split_allowed_image_types(cls, v: str) -> List[str]:
        return [x.strip() for x in v.split(",") if x.strip()]

    class Config:
        env_file = ".api_env"
        env_file_encoding = "utf-8"


settings = Settings()
