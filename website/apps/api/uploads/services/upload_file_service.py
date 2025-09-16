from pathlib import Path

from django.db import transaction
from django.utils import timezone
from library.aws.client.s3 import PresignedMultipart, S3UploadClient

from apps.api.uploads.models import LazyLoadFile, get_lazy_file_path


class UploadFileService:
    def __init__(self, client: S3UploadClient = None):
        self.client = client

    def upload(
        self,
        file_name: str,
        file_size: int,
        content_type: str,
        key: str = None,
    ) -> tuple[LazyLoadFile, PresignedMultipart]:
        name = Path(file_name).name

        key = key or get_lazy_file_path(LazyLoadFile, file_name)
        multipart = self.client.get_presigned_multipart(
            key=key,
            file_size=file_size,
            content_type=content_type,
        )

        file_extension = Path(file_name).suffix[1:]
        file = LazyLoadFile.objects.create(
            file=key,
            name=name,
            file_name=file_name,
            file_extension=file_extension,
            upload_id=multipart.upload_id,
        )
        return file, multipart

    @transaction.atomic
    def abort(self, file: LazyLoadFile):
        key = str(file.file)
        file.status = LazyLoadFile.Status.CANCELED
        file.finished_at = timezone.now()
        file.save()
        self.client.abort_multipart_upload(
            key=key,
            upload_id=file.upload_id,
        )

    @transaction.atomic
    def complete(self, file: LazyLoadFile, etags: list[str]):
        file.status = LazyLoadFile.Status.COMPLETED
        key = str(file.file)
        file.finished_at = timezone.now()
        file.save()
        self.client.complete_multipart_upload(
            key=key,
            upload_id=file.upload_id,
            etags=etags,
        )

    @property
    def client(self) -> S3UploadClient:
        return self._client

    @client.setter
    def client(self, client: S3UploadClient = None):
        if client is None:
            client = S3UploadClient()
        self._client = client
