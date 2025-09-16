import math
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from .storage_client import S3StorageClient


@dataclass
class PresignedMultipart:
    urls: list[str]
    upload_id: str


class S3UploadClient(S3StorageClient):
    def get_presigned_multipart(
        self,
        key: str,
        content_type: str,
        file_size: int,
        # Value in seconds
        expires: int = 3600,
        bucket: str = settings.AWS_STORAGE_BUCKET_NAME,
        chunk_size: int | None = settings.UPLOAD_CHUNK_SIZE
    ) -> PresignedMultipart:

        total_chunks = math.ceil(file_size / chunk_size)

        payload = {
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        }
        data = self.client.create_multipart_upload(**payload)
        upload_id = data["UploadId"]
        urls = []

        for i in range(1, total_chunks + 1):
            signed_url = self.client.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": bucket,
                    "Key": key,
                    "PartNumber": i,
                    "UploadId": upload_id,
                },
                ExpiresIn=expires,
            )
            urls.append(signed_url)

        presigned_multipart = PresignedMultipart(
            urls=urls,
            upload_id=upload_id,
        )

        return presigned_multipart

    def abort_multipart_upload(
        self,
        key: str,
        upload_id: str,
        bucket: str = settings.AWS_STORAGE_BUCKET_NAME,
    ):
        self.client.abort_multipart_upload(
            Key=key,
            UploadId=upload_id,
            Bucket=bucket,
        )

    def upload_file(
        self,
        key: str,
        local_path: Path,
        bucket: str = settings.AWS_STORAGE_BUCKET_NAME,
        extra: dict = None
    ) -> None:
        extra = extra or {}
        suffix = local_path.suffix.lower()
        if suffix == ".m3u8":
            extra["ContentType"] = "application/vnd.apple.mpegurl"
            extra["CacheControl"] = "public, max-age=31536000, immutable"
        elif suffix == ".ts":
            extra["ContentType"] = "video/mp2t"
            extra["CacheControl"] = "public, max-age=31536000, immutable"
        elif suffix == ".key":
            extra["ContentType"] = "application/octet-stream"
            extra["CacheControl"] = "no-cache"

        self.client.upload_file(str(local_path), bucket, key, ExtraArgs=extra)

    def complete_multipart_upload(
        self,
        key: str,
        upload_id: str,
        etags: list[str],
        bucket: str = settings.AWS_STORAGE_BUCKET_NAME,
    ):
        parts = [{"ETag": etags[i], "PartNumber": i + 1} for i in range(len(etags))]
        self.client.complete_multipart_upload(
            Key=key,
            UploadId=upload_id,
            Bucket=bucket,
            MultipartUpload={"Parts": parts},
        )
