from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet

from apps.api.cinema.videos.models import Video


class VideoSearchService:
    @staticmethod
    def search(value: str, queryset: QuerySet[Video] = None) -> QuerySet[Video]:
        queryset = queryset or Video.objects.all()

        return (
            queryset
            .annotate(similarity=TrigramSimilarity("file__name", value))
            .order_by("-similarity")
        )
