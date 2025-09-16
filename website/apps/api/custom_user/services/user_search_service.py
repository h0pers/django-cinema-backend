from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet

User = get_user_model()


class UserSearchService:
    @staticmethod
    def search(query: str, queryset: QuerySet[User]) -> QuerySet[User]:
        queryset = queryset or User.objects.all()

        if not query:
            return queryset.none()

        qs = (
            Q(email__iexact=query) |
            Q(stripe_customer_id__iexact=query)
        )

        return queryset.filter(qs)
