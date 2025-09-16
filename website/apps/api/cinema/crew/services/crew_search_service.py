from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet

from apps.api.cinema.crew.models import CrewMember


class CrewSearchService:
    @staticmethod
    def search(query: str, queryset: QuerySet[CrewMember] = None) -> QuerySet[CrewMember]:
        queryset = queryset or CrewMember.objects.all()
        return (
            queryset.annotate(
                similarity=TrigramSimilarity("full_name", query),
            )
            .order_by("-similarity")
        )
