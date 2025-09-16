import uuid

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower

from apps.core.validators import FilenameExtensionValidator

VIDEO_EXTENSIONS: tuple[str] = ("mp4",)
AUDIO_EXTENSIONS: tuple[str] = ("mp3",)


def get_lazy_file_path(_, filename) -> str:
    return f"uploads/{filename}"


class LazyLoadFile(models.Model):
    class FileType(models.TextChoices):
        AUDIO = "audio"
        VIDEO = "video"
        INVALID = "invalid"

    class Status(models.TextChoices):
        LOADING = "loading"
        COMPLETED = "completed"
        CANCELED = "canceled"
        EXPIRED = "expired"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        upload_to=get_lazy_file_path,
        null=True,
        blank=True,
    )
    # Use this field for searching and naming (Application version of file_name).
    # Do not change file_name, use this field instead.
    name = models.CharField(max_length=255)
    # Status of loading
    status = models.CharField(choices=Status.choices, default=Status.LOADING, max_length=20)
    # filename.mp4
    file_name = models.CharField(
        max_length=255,
        validators=[
            FilenameExtensionValidator(
                settings.ALLOWED_UPLOAD_FILE_EXTENSIONS,
            )
        ]
    )
    # mp4, mp3 etc.
    file_extension = models.CharField(editable=False, max_length=255)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, editable=False)
    upload_id = models.CharField(max_length=255, editable=False)

    class Meta:
        ordering = ["-finished_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_file",
            ),
            models.UniqueConstraint(
                Lower("file_name"),
                name="unique_file_name",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def loading(self) -> bool:
        return self.status == LazyLoadFile.Status.LOADING

    @property
    def completed(self) -> bool:
        return self.status == LazyLoadFile.Status.COMPLETED

    @property
    def canceled(self) -> bool:
        return self.status == LazyLoadFile.Status.CANCELED

    @property
    def file_type(self) -> str:
        """
        Calculates the file type based on the file extension
        """
        extension_to_type = {
            AUDIO_EXTENSIONS: self.FileType.AUDIO,
            VIDEO_EXTENSIONS: self.FileType.VIDEO,
        }
        flat_extension = {
            extension: file_type
            for extensions, file_type in extension_to_type.items()
            for extension in extensions
        }
        return flat_extension.get(self.file_extension, self.FileType.INVALID)

    @property
    def is_audio(self) -> bool:
        return self.file_type == self.FileType.AUDIO

    @property
    def is_video(self) -> bool:
        return self.file_type == self.FileType.VIDEO
