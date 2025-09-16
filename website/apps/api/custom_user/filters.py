from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from apps.api.custom_user.models import UserSubscription
from apps.api.custom_user.services.user_search_service import UserSearchService

User = get_user_model()


class UserFilterSet(filters.FilterSet):
    date_joined = filters.DateFromToRangeFilter()
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = User
        fields = [
            "date_joined",
            "is_staff",
            "is_superuser",
            "is_active",
        ]

    def filter_search(self, queryset, _, value):
        return UserSearchService.search(value, queryset)


class UserSubscriptionFilterSet(filters.FilterSet):
    class Meta:
        model = UserSubscription
        fields = "__all__"
