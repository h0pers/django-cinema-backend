from pathlib import Path

from botocore.client import BaseClient
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import storages
from storages.backends.s3 import S3Storage

from .base_storage_client import StorageClientBase


class S3StorageClient(StorageClientBase[S3Storage, BaseClient]):
    def _get_default_storage(self) -> S3Storage:
        storage = storages["default"]
        if not isinstance(storage, S3Storage):
            raise ImproperlyConfigured("Storage must be an instance of S3Storage")
        return storage

    def _expected_storage_type(self) -> type[S3Storage]:
        return S3Storage

    def _client_from_storage(self, storage: S3Storage) -> BaseClient:
        return storage.connection.meta.client

    def delete_prefix(self, prefix: str, bucket: str = settings.AWS_STORAGE_BUCKET_NAME) -> None:
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        to_delete = []
        for page in pages:
            contents = page.get("Contents", [])
            for obj in contents:
                to_delete.append({"Key": obj["Key"]})
                # пачками по 1000
                if len(to_delete) == 1000:
                    self.client.delete_objects(Bucket=bucket, Delete={"Objects": to_delete})
                    to_delete.clear()
        if to_delete:
            self.client.delete_objects(Bucket=bucket, Delete={"Objects": to_delete})

    def download_to(self, key: str, local_path: Path, bucket: str = settings.AWS_STORAGE_BUCKET_NAME) -> None:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            self.client.download_fileobj(bucket, key, f)
