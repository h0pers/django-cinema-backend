from django_filters import rest_framework as filters

from apps.api.cinema.seasons.models import Season
from apps.core.services.descriptive_search_service import DescriptiveSearchService


class SeasonFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Season
        fields = [
            "search",
        ]

    def filter_search(self, queryset, _, value):
        return DescriptiveSearchService.search(queryset, value)
