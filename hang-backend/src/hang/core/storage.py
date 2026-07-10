import logging
import boto3
from botocore.config import Config
from typing import List

from hang.schemas.config import conf

logger = logging.getLogger("Hang")


class StorageService:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=conf.R2_ENDPOINT,
            aws_access_key_id=conf.R2_ACCESS_KEY_ID,
            aws_secret_access_key=conf.R2_SECRET_ACCESS_KEY,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

        self.bucket = conf.R2_BUCKET_NAME

    def build_image_url(self, key: str) -> str:
        logger.info(
            "hang_event",
            extra={
                "event": "storage_presign",
                "status": "success",
                "context": {"key": key},
            },
        )

        return self.s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
            },
            ExpiresIn=3600,
        )

    def upload(self, key: str, contents: bytes, ext: str) -> None:
        try:
            logger.info(
                "hang_event",
                extra={
                    "event": "storage_upload",
                    "status": "starting",
                    "context": {"key": key},
                },
            )

            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=contents,
                ContentType=f"image/{ext}",
            )

            logger.info(
                "hang_event",
                extra={
                    "event": "storage_upload",
                    "status": "success",
                    "context": {"key": key},
                },
            )

        except Exception as exc:
            logger.error(
                "hang_event",
                extra={
                    "event": "storage_upload",
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "context": {"key": key},
                },
            )
            raise

    def upload_many(self, files: list[tuple[str, bytes, str]]) -> None:
        for key, contents, ext in files:
            self.upload(key, contents, ext)

    def delete_many(self, keys: List[str]) -> None:
        for key in keys:
            try:
                logger.info(
                    "hang_event",
                    extra={
                        "event": "storage_delete",
                        "status": "starting",
                        "context": {"key": key},
                    },
                )
                self.s3.delete_object(Bucket=self.bucket, Key=key)
                logger.info(
                    "hang_event",
                    extra={
                        "event": "storage_delete",
                        "status": "success",
                        "context": {"key": key},
                    },
                )

            except Exception as exc:
                logger.error(
                    "hang_event",
                    extra={
                        "event": "storage_delete",
                        "status": "failed",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "context": {"key": key},
                    },
                )


storage_service = StorageService()


def get_storage() -> StorageService:
    return storage_service
