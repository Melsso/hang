from botocore.config import Config
from typing import List
import boto3

from hang.schemas.config import settings

# TODO turn this to a class, write methods to perform tasks rather than repetitive code
s3 = boto3.client(
    "s3",
    endpoint_url=settings.R2_ENDPOINT,
    aws_access_key_id=settings.R2_ACCESS_KEY_ID,
    aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=Config(signature_version="s3v4"),
)


def build_image_url(key: str) -> str:
    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=3600,
    )


def upload_s3_element(key: str, contents: bytes, ext: str) -> None:
    s3.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=contents,
        ContentType=f"image/{ext}",
    )


def upload_s3_elements(files: list[tuple[str, bytes, str]]) -> None:
    for key, contents, ext in files:
        upload_s3_element(
            key=key,
            contents=contents,
            ext=ext,
        )


def delete_s3_elements(keys: List[str]) -> None:
    for key in keys:
        s3.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
