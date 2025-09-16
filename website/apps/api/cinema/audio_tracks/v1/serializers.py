from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.api.cinema.audio_tracks.models import AudioTrack
from apps.core.models import Language


class AudioTrackSerializer(serializers.ModelSerializer):
    language = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.all(),
    )

    class Meta:
        model = AudioTrack
        fields = [
            "id",
            "is_default",
            "file",
            "language",
            "video",
        ]

    def validate_file(self, value):
        if not value.is_audio:
            raise ValidationError(_("File is not audio type"))
        return value
