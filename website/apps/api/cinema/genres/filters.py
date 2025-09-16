from django_filters import rest_framework as filters

from apps.api.cinema.genres.models import Genre
from apps.api.cinema.genres.services.genre_search_service import GenreSearchService


class GenreFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Genre
        fields = [
            "search",
        ]

    def filter_search(self, queryset, _, value):
        return GenreSearchService.search(value, queryset)


