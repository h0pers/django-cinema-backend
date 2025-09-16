import django_filters.rest_framework as filters
from utils.intervals import Interval

from apps.core.services.descriptive_search_service import DescriptiveSearchService

from .models import Product


class ProductFilterSet(filters.FilterSet):
    order_by = filters.OrderingFilter(
        fields=(
            ('final_price', 'final_price'),
        )
    )
    subscription_interval_count = filters.NumberFilter(
        field_name="subscription__billing_interval_count",
    )
    subscription_interval= filters.ChoiceFilter(
        choices=Interval.choices,
        field_name="subscription__billing_interval",
    )
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Product
        fields = [
            "status",
            "type",
        ]

    def filter_search(self, queryset, _, value):
        return DescriptiveSearchService.search(value, queryset)
