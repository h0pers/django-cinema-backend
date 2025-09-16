import uuid
from functools import partial
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from library.aws.client.s3 import S3UploadClient

from apps.api.uploads.models import LazyLoadFile
from apps.core.models import Language


class ToggleWatchModel(models.Model):
    # Use this field to toggle watch availability to customers
    # Remember it is watch switcher for staff, but doesn't mean it is ready to watch
    allowed_to_watch = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Video(models.Model):
    class Status(models.TextChoices):
        CREATED = "created"
        # FFmpeg processing started
        PROCESSING = "processing"
        # HLS files created
        COMPLETED = "completed"
        # Processing failed
        FAILED = "failed"

    class Visibility(models.TextChoices):
        # Doesn't check permissions
        PUBLIC = "public"
        # Enables permissions check
        PROTECTED = "protected"

    class Role(models.TextChoices):
        MOVIE = "movie"
        EPISODE = "episode"
        TRAILER = "trailer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(choices=Status.choices, default=Status.CREATED, max_length=20)
    visibility = models.CharField(choices=Visibility.choices, default=Visibility.PROTECTED, max_length=20)
    role = models.CharField(choices=Role.choices, max_length=20)
    file = models.OneToOneField(
        LazyLoadFile,
        on_delete=models.PROTECT,
    )
    hls_master_playlist = models.FileField(null=True, blank=True)
    hls_decrypt_key = models.FileField(null=True, blank=True, editable=False)
    original_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    languages = models.ManyToManyField(
        Language,
        through="AudioTrack",
        related_name="video_languages",
    )
    rebuild_needed = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return str(self.file)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.hls_master_playlist:
            # Cleaning all files
            upload_client = S3UploadClient()
            # Removing all in video directory, including a url version
            video_directory_path = str(Path(str(self.hls_master_playlist)).parent.parent)
            transaction.on_commit(partial(
                upload_client.delete_prefix,
                video_directory_path,
            ))
        super().delete(*args, **kwargs)

    def clean(self):
        if (
            self.attached_as_movie and
            self.role != self.Role.MOVIE
        ):
            raise ValidationError(_("Video attached to a movie, please resolve it before changing role"))

        if (
            self.attached_as_episode and
            self.role != self.Role.EPISODE
        ):
            raise ValidationError(_("Video attached to an episode, please resolve it before changing role"))

        if (
            self.attached_as_trailer and
            self.role != self.Role.TRAILER
        ):
            raise ValidationError(_("Video attached to a movie as trailer, please resolve it before changing role"))

        super().clean()

    @property
    def has_default_audio(self) -> bool:
        return self.audio_tracks.filter(is_default=True).exists()

    @property
    def encrypted(self) -> bool:
        return bool(self.hls_decrypt_key)

    @property
    def processing(self) -> bool:
        return self.status == Video.Status.PROCESSING

    @property
    def completed(self) -> bool:
        return self.status == Video.Status.COMPLETED

    @property
    def public(self) -> bool:
        return self.visibility == self.Visibility.PUBLIC

    @property
    def protected(self) -> bool:
        return self.visibility == self.Visibility.PROTECTED

    @property
    def attached_as_movie(self) -> bool:
        return hasattr(self, "as_movie")

    @property
    def attached_as_episode(self) -> bool:
        return hasattr(self, "as_episode")

    @property
    def attached_as_trailer(self) -> bool:
        return hasattr(self, "as_trailer")


class VideoResolution(models.Model):
    class Resolution(models.IntegerChoices):
        P1080 = 1080, "1080p"
        P720 = 720, "720p"
        P480 = 480, "480p"
        P360 = 360, "360p"

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='resolutions',
    )
    resolution = models.PositiveSmallIntegerField(choices=Resolution.choices)
    file = models.FileField()

    class Meta:
        ordering = ["-resolution"]
        constraints = [
            models.UniqueConstraint(
                fields=["video", "resolution"],
                name="unique_video_resolution",
            )
        ]

    def __str__(self):
        return self.get_resolution_display()
