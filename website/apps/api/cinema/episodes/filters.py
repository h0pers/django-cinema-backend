from django_filters import rest_framework as filters

from apps.api.cinema.episodes.models import Episode
from apps.core.services.descriptive_search_service import DescriptiveSearchService


class EpisodeFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    publication_date = filters.DateFromToRangeFilter()

    class Meta:
        model = Episode
        fields = [
            "publication_date",
            "allowed_to_watch",
        ]

    def filter_search(self, queryset, _, value):
        return DescriptiveSearchService.search(value, queryset)
