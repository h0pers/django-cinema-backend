from django_filters import rest_framework as filters
from django_filters.constants import EMPTY_VALUES

from apps.api.cinema.crew.models import CrewMember
from apps.api.cinema.genres.models import Genre
from apps.core.models import Language
from apps.core.services.descriptive_search_service import DescriptiveSearchService

from .models import Title, TitleCrewMember
from .services.title_search_service import TitleSearchService


class CrewPositionChainFilter(filters.BaseInFilter, filters.CharFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("distinct", True)
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        """
        ?crew=124:actor,987:director provides AND for each pair.
        Title must contain (124, actor) AND (987, director).
        """
        if value in EMPTY_VALUES:
            return qs

        pairs = []

        for pair in value:
            if ':' in pair:
                pid, pos = pair.split(':', 1)
                pid = pid.strip()

                if not pid.isdigit():
                    continue

                pos = pos.strip()
                if pid and pos:
                    pairs.append((pid, pos))
        for pid, pos in pairs:
            qs = qs.filter(
                crew_members__crew_member=pid,
                crew_members__position__iexact=pos
            )

        if self.distinct:
            qs = qs.distinct()

        return qs


class TitleCrewMemberFilterSet(filters.FilterSet):
    position = filters.MultipleChoiceFilter(choices=TitleCrewMember.Position.choices)

    class Meta:
        model = TitleCrewMember
        fields = ['position']


class TitleFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    release_date = filters.DateFromToRangeFilter()
    release_year_range = filters.RangeFilter(
        field_name="release_year",
    )
    languages = filters.ModelMultipleChoiceFilter(
        field_name="languages__code",
        to_field_name="code",
        queryset=Language.objects.all(),
    )
    genres = filters.ModelMultipleChoiceFilter(
        field_name="genres__slug",
        to_field_name="slug",
        queryset=Genre.objects.all(),
    )
    crew_members = filters.ModelMultipleChoiceFilter(
        field_name="crew_members__crew_member",
        queryset=CrewMember.objects.all(),
    )
    crew_members_positions = filters.MultipleChoiceFilter(
        field_name="crew_members__position",
        choices=TitleCrewMember.Position.choices,
    )
    # Chain crew members-to-positions
    # ?crew=124:actor,987:director
    crew_member_to_position = CrewPositionChainFilter()
    released = filters.BooleanFilter(method="filter_released")

    class Meta:
        model = Title
        fields = [
            "type",
            "status",
            "release_year",
            "allowed_to_watch",
        ]

    def filter_search(self, queryset, _, value):
        return DescriptiveSearchService.search(value, queryset)

    def filter_released(self, queryset, _, value):
        if not value:
            return TitleSearchService.not_released(queryset)
        return TitleSearchService.released(queryset)
