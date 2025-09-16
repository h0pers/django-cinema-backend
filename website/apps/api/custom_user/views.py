from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import DjangoModelPermissions, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.api.custom_user.filters import UserFilterSet, UserSubscriptionFilterSet
from apps.api.custom_user.models import CustomGroup, UserSubscription
from apps.api.custom_user.services.user_subscription_service import UserSubscriptionService
from apps.api.custom_user.v1.serializers import (
    BillingUserSubscriptionSerializer,
    GroupSerializer,
    PermissionSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionStaffSerializer,
)
from apps.api.mixins import VersioningAPIViewMixin
from apps.api.payments.orders.filters import OrderFilterSet
from apps.api.payments.orders.v1.serializers import OrderSerializer
from apps.api.payments.transactions.filters import TransactionFilterSet
from apps.api.payments.transactions.v1.serializers import TransactionSerializer, TransactionStaffSerializer

User = get_user_model()


class UserViewSet(VersioningAPIViewMixin, ModelViewSet):
    queryset = User.objects.all()
    filterset_class = UserFilterSet
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    version_map = {
        "v1": {
            "serializer_class": UserSerializer
        }
    }

    def get_queryset(self):
        if self.action == "my_orders":
            return self.request.user.orders.all()

        if self.action == "my_subscriptions":
            return self.request.user.subscriptions.all()

        if self.action == "my_transactions":
            return self.request.user.transactions.all()

        return super().get_queryset()

    def get_version_map(self):
        if not self.request.user.is_staff:
            if self.action == "my_subscriptions":
                return {
                    "v1": {
                        "serializer_class": UserSubscriptionStaffSerializer,
                    }
                }
            if self.action == "my_transactions":
                return {
                    "v1": {
                        "serializer_class": TransactionSerializer
                    }
                }
        return super().get_version_map()

    @action(
        methods=['GET'],
        detail=False,
        url_path="me/orders",
        permission_classes=[IsAuthenticated],
        filterset_class=OrderFilterSet,
        version_map={
            "v1": {
                "serializer_class": OrderSerializer
            }
        }
    )
    def my_orders(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=False,
        url_path="me/transactions",
        filterset_class=TransactionFilterSet,
        permission_classes=[IsAuthenticated],
        version_map={
            "v1": {
                "serializer_class": TransactionStaffSerializer
            }
        }
    )
    def my_transactions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @action(
        methods=['GET'],
        detail=False,
        url_path="me/subscriptions",
        permission_classes=[IsAuthenticated],
        filterset_class=UserSubscriptionFilterSet,
        version_map={
            "v1": {
                "serializer_class": UserSubscriptionSerializer
            }
        }
    )
    def my_subscriptions(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class PermissionViewSet(
    VersioningAPIViewMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Permission.objects.all()
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    version_map = {
        "v1": {
            "serializer_class": PermissionSerializer
        }
    }


class GroupViewSet(
    VersioningAPIViewMixin,
    ModelViewSet
):
    queryset = CustomGroup.objects.all()
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    version_map = {
        "v1": {
            "serializer_class": GroupSerializer
        }
    }


class UserSubscriptionViewSet(
    VersioningAPIViewMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = UserSubscription.objects.all()
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    version_map = {
        "v1": {
            "serializer_class": UserSubscriptionSerializer
        }
    }

    def get_version_map(self):
        if self.request.user.is_staff and self.action in ("create", "retrieve", "list"):
            return {
                "v1": {
                    "serializer_class": UserSubscriptionStaffSerializer,
                }
            }
        return super().get_version_map()

    def get_queryset(self):
        if (
            self.action in ("retrieve", "cancel") and
            not self.request.user.is_staff
        ):
            return self.request.user.subscriptions.all()
        return super().get_queryset()

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[DjangoModelPermissions, IsAdminUser],
        version_map=None
    )
    def disable(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)
        if obj.disabled:
            raise ValidationError({"subscription": _("User subscription already disabled")})
        UserSubscriptionService.disable(obj)
        return Response({"message": _("Subscription disabled")})

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[IsAuthenticated],
        version_map=None
    )
    def cancel(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)

        if obj.canceled:
            raise ValidationError({"subscription": _("User subscription already cancelled")})

        UserSubscriptionService.cancel(obj)
        return Response({"message": _("Subscription cancelled")})

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[DjangoModelPermissions, IsAdminUser],
        version_map={
            "v1": {
                "serializer_class": BillingUserSubscriptionSerializer,
            }
        }
    )
    def billing(self, request, *args, **kwargs):
        obj = self.get_object()
        self.check_object_permissions(request, obj)

        if obj.disabled:
            raise ValidationError({"subscription": _("Subscription disabled")})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        billing_date = serializer.validated_data["next_billing_date"]

        UserSubscriptionService.extend(obj, billing_date, merchant_update=True)
        return Response({"message": _("Subscription billing date updated")})
