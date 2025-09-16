from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.api.cinema.videos.models import Video
from apps.api.uploads.models import LazyLoadFile
from apps.core.models import Language


class AudioTrack(models.Model):
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="audio_tracks",
    )
    hls_file = models.FileField(editable=False)
    # This field reference to the source of audio
    file = models.OneToOneField(
        LazyLoadFile,
        on_delete=models.PROTECT,
        related_name='as_audio_track',
        null=True,
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["video", "language"],
                name="unique_video_language",
            ),
            models.UniqueConstraint(
                fields=["video", "is_default"],
                condition=models.Q(is_default=True),
                name="unique_video_is_default",
            )
        ]

    def __str__(self):
        return str(self.file)

    def clean(self):
        if self.is_default and self.video.has_default_audio:
            raise ValidationError(_("Only one audio track can be set as default"))
