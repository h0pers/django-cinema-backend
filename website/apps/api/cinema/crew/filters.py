from django_filters import rest_framework as filters

from apps.api.cinema.titles.models import TitleCrewMember

from .models import CrewMember
from .services.crew_search_service import CrewSearchService


class CrewMemberFilterSet(filters.FilterSet):
    search = filters.CharFilter(method='filter_search')
    positions = filters.MultipleChoiceFilter(
        field_name="titles__position",
        choices=TitleCrewMember.Position.choices,
    )

    class Meta:
        model = CrewMember
        fields = [
            "search"
        ]

    def filter_search(self, queryset, _, value):
        return CrewSearchService.search(value, queryset)
