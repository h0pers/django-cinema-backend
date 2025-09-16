from django.db.models import QuerySet

from apps.api.payments.orders.models import Order


class OrderSearchService:
    @staticmethod
    def search(query: str, queryset: QuerySet[Order]) -> QuerySet[Order]:
        queryset = queryset or Order.objects.all()
        if not query:
            return queryset.none()
        return queryset.filter(id__iexact=query)
