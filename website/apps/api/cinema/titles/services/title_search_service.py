from datetime import UTC, datetime

from django.db.models import Q, QuerySet

from apps.api.cinema.titles.models import Title


class TitleSearchService:
    @classmethod
    def _released_query(cls) -> Q:
        now = datetime.now(UTC)
        return Q(
            release_date__isnull=False,
            release_year__isnull=False,
            release_date__lte=now,
            release_year__lte=now.year,
        )

    @classmethod
    def released(cls, queryset: QuerySet[Title] = None) -> QuerySet[Title]:
        queryset = queryset or Title.objects.all()
        return queryset.filter(cls._released_query())

    @classmethod
    def not_released(cls, queryset: QuerySet[Title] = None) -> QuerySet[Title]:
        queryset = queryset or Title.objects.all()
        return queryset.exclude(cls._released_query())
