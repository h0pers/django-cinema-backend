import django_filters.rest_framework as filters

from apps.api.cinema.videos.models import Video, VideoResolution
from apps.api.cinema.videos.services.video_search_service import VideoSearchService
from apps.api.uploads.models import LazyLoadFile
from apps.core.models import Language


class VideoFilterSet(filters.FilterSet):
    original_language = filters.ModelChoiceFilter(
        field_name="original_language__code",
        to_field_name="code",
        queryset=Language.objects.all(),
    )
    languages = filters.ModelMultipleChoiceFilter(
        field_name="languages__code",
        to_field_name="code",
        queryset=Language.objects.all(),
        conjoined=True,
    )
    search = filters.CharFilter(method="filter_search")
    files = filters.ModelMultipleChoiceFilter(
        field_name="file",
        queryset=LazyLoadFile.objects.all(),
    )
    resolutions = filters.MultipleChoiceFilter(
        field_name="resolutions__resolution",
        choices=VideoResolution.Resolution.choices,
        conjoined=True,
    )
    roles = filters.MultipleChoiceFilter(
        field_name="role",
        choices=Video.Role.choices,
    )

    class Meta:
        model = Video
        fields = [
            "visibility",
            "status",
            "roles",
            "search",
            "files",
            "resolutions",
            "original_language",
            "languages",
            "rebuild_needed",
        ]

    def filter_search(self, queryset, _, value):
        return VideoSearchService.search(value, queryset)
