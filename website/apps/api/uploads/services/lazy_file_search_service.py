from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import QuerySet

from apps.api.uploads.models import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, LazyLoadFile


class LazyFileSearchService:
    @staticmethod
    def search(value: str, queryset: QuerySet[LazyLoadFile] = None) -> QuerySet[LazyLoadFile]:
        queryset = queryset or LazyLoadFile.objects.all()
        return (
            queryset
            .annotate(similarity=TrigramSimilarity("name", value))
            .order_by("-similarity")
        )

    @staticmethod
    def audios(queryset: QuerySet[LazyLoadFile] = None) -> QuerySet[LazyLoadFile]:
        queryset = queryset or LazyLoadFile.objects.all()
        print()
        return queryset.filter(
            file_extension__in=AUDIO_EXTENSIONS,
        )

    @staticmethod
    def videos(queryset: QuerySet[LazyLoadFile] = None) -> QuerySet[LazyLoadFile]:
        queryset = queryset or LazyLoadFile.objects.all()
        return queryset.filter(
            file_extension__in=VIDEO_EXTENSIONS,
        )



