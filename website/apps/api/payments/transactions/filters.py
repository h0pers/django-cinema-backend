from django_filters import rest_framework as filters

from apps.api.payments.transactions.models import Transaction
from apps.api.payments.transactions.services.transaction_search_service import TransactionSearchService


class TransactionFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Transaction
        fields = [
            "paid",
            "payment_provider",
        ]

    def filter_search(self, queryset, _, value):
        return TransactionSearchService.search(value, queryset)
