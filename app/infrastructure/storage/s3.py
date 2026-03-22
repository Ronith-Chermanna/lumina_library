"""S3-compatible (MinIO / AWS) storage adapter."""

from __future__ import annotations

import logging

import boto3
from botocore.exceptions import ClientError

from app.domain.interfaces.storage import StorageInterface

logger = logging.getLogger(__name__)


class S3Storage(StorageInterface):
    """Stores book files in an S3-compatible bucket (e.g. MinIO or AWS S3)."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1",
    ) -> None:
        self._bucket = bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        # Ensure bucket exists
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            self._client.create_bucket(Bucket=self._bucket)
            logger.info("Created S3 bucket %s", self._bucket)

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info("Uploaded %s to S3 (%s, %d bytes)", key, content_type, len(data))
        return key

    async def retrieve(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)
        logger.info("Deleted %s from S3", key)

    async def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False
