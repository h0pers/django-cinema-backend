from django.db.models import Q, QuerySet

from apps.core.models import Language


class LanguageSearchService:
    @staticmethod
    def search(value: str, queryset: QuerySet[Language] = None) -> QuerySet[Language]:
        queryset = queryset or Language.objects.all()
        return queryset.filter(
            Q(code__icontains=value) | Q(name__icontains=value)
        )
