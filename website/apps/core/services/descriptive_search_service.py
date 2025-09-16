from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.db.models import Case, FloatField, Q, QuerySet, Value, When
from django.db.models.functions import Coalesce

from apps.core.models import DescriptiveModel


class DescriptiveSearchService:
    @staticmethod
    def search(
        query: str,
        queryset: QuerySet[DescriptiveModel],
        fuzzy_weight: float = 0.35,
        prefix_boost: float = 0.4,
        exact_boost: float = 1.0,
        trigram_threshold: float = 0.25,
    ) -> QuerySet[DescriptiveModel]:

        if not query:
            return queryset.none()

        search_query = SearchQuery(query, search_type="websearch", config="simple")
        search_vector = (
            SearchVector("name", weight="A", config="simple") +
            SearchVector("description", weight="B", config="simple")
        )

        qs = (
            queryset
            .annotate(
                rank=SearchRank(search_vector, search_query),
                similarity=TrigramSimilarity("name", query),
                exact_match=Case(
                    When(name__iexact=query, then=Value(exact_boost)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                prefix_match=Case(
                    When(name__istartswith=query, then=Value(prefix_boost)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
            )
            .filter(
                Q(rank__gt=0.0) |
                Q(similarity__gt=trigram_threshold) |
                Q(name__icontains=query)
            )
        )

        qs = qs.annotate(
            score=Coalesce(
                Value(0.0, output_field=FloatField()) +
                (Value(1.0) * qs.query.annotations["rank"]) +
                (Value(fuzzy_weight) * qs.query.annotations["similarity"]) +
                qs.query.annotations["exact_match"] +
                qs.query.annotations["prefix_match"],
                Value(0.0),
                output_field=FloatField(),
            )
        ).order_by("-score", "-rank")

        return qs
