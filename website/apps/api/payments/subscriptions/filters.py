from django_filters import rest_framework as filters

from apps.api.payments.subscriptions.models import Subscription
from apps.core.services.descriptive_search_service import DescriptiveSearchService


class SubscriptionFilterSet(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Subscription
        exclude = [
            "name",
            "description",
        ]

    def filter_search(self, queryset, _, value):
        return DescriptiveSearchService.search(value, queryset)
