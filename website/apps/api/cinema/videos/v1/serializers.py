from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.api.cinema.videos.models import Video
from apps.api.languages.v1.serializers import LanguageSerializer
from apps.api.uploads.models import LazyLoadFile
from apps.core.models import Language


class VideoLazyFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LazyLoadFile
        fields = [
            "id",
            "name",
        ]
        read_only_fields = [
            "name",
        ]


class VideoSerializer(serializers.ModelSerializer):
    resolutions = serializers.SerializerMethodField()
    languages = LanguageSerializer(
        many=True,
        read_only=True,
    )
    original_language_id = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Language.objects.all(),
        allow_null=True,
        required=False,
        write_only=True,
    )
    original_language = LanguageSerializer(
        read_only=True,
    )
    file = VideoLazyFileSerializer(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "status",
            "file",
            "visibility",
            "role",
            "resolutions",
            "original_language_id",
            "original_language",
            "languages",
            "rebuild_needed",
            "as_movie",
            "as_trailer",
            "as_episode",
        ]
        read_only_fields = [
            "status",
            "as_movie",
            "as_trailer",
            "as_episode",
        ]

    def validate_file(self, value):
        if not value.completed:
            raise ValidationError(_("File is still loading"))
        if not value.is_video:
            raise ValidationError(_("File is not a video"))
        return value

    def get_resolutions(self, obj) -> list[str]:
        return [resolution.get_resolution_display() for resolution in obj.resolutions.all()]


class VideoCreateSerializer(VideoSerializer):
    # Set null to use default field
    file = None


class PlaybackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            "hls_master_playlist",
        ]
