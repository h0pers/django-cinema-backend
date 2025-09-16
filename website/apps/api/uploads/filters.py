from collections.abc import Sequence

import django_filters.rest_framework as filters

from apps.api.uploads.models import LazyLoadFile
from apps.api.uploads.services.lazy_file_search_service import LazyFileSearchService


class FileExtensionFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class LazyFileFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    type = filters.MultipleChoiceFilter(
        method="filter_file_types",
        choices=LazyLoadFile.FileType.choices,
    )
    file_extension = FileExtensionFilter()

    class Meta:
        model = LazyLoadFile
        fields = [
            "status",
            "search",
            "type",
            "file_extension",
        ]

    def filter_file_types(self, queryset, _, value: Sequence[str]):
        if LazyLoadFile.FileType.AUDIO in value:
            queryset = LazyFileSearchService.audios(queryset)

        if LazyLoadFile.FileType.VIDEO in value:
            queryset = LazyFileSearchService.videos(queryset)

        return queryset

    def filter_search(self, queryset, _, value):
        return LazyFileSearchService.search(value, queryset)
