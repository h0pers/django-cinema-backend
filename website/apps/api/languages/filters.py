from django_filters import rest_framework as filters

from apps.api.languages.services.language_search_service import LanguageSearchService
from apps.core.models import Language


class LanguageFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Language
        fields = [
            "search",
        ]

    def filter_search(self, queryset, _, value):
        return LanguageSearchService.search(value, queryset)
