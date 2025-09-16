from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet

from apps.api.cinema.genres.models import Genre


class GenreSearchService:
    @staticmethod
    def search(query: str, queryset: QuerySet[Genre] = None) -> QuerySet[Genre]:
        queryset = queryset or Genre.objects.all()
        return (
            queryset
            .annotate(similarity=TrigramSimilarity("name", query))
            .order_by("-similarity")
        )
