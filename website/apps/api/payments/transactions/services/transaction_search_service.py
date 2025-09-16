from django.db.models import Q, QuerySet

from apps.api.payments.transactions.models import Transaction


class TransactionSearchService:
    @staticmethod
    def search(query: str, queryset: QuerySet[Transaction]) -> QuerySet[Transaction]:
        queryset = queryset or Transaction.objects.all()

        if not query:
            return queryset.none()

        return queryset.filter(
            Q(id__iexact=query) |
            Q(external_payment_id__iexact=query)
        )
