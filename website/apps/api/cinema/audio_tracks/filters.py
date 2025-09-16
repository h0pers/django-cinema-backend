from django_filters import rest_framework as filters

from apps.api.cinema.audio_tracks.models import AudioTrack
from apps.core.models import Language


class AudioTrackFilter(filters.FilterSet):
    language = filters.ModelMultipleChoiceFilter(
        field_name="language__code",
        to_field_name="code",
        queryset=Language.objects.all(),
    )

    class Meta:
        model = AudioTrack
        fields = [
            "language",
            "is_default",
        ]
