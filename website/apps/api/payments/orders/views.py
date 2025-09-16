from django.db import transaction
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import DjangoModelPermissions, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from apps.api.mixins import VersioningAPIViewMixin

from .filters import OrderFilterSet
from .models import Order, OrderItem
from .services.order_creation_service import OrderCreationService
from .services.order_payment_service import OrderPaymentService
from .v1.serializers import (
    CheckoutItemCreateSerializer,
    CheckoutResponseSerializer,
    CheckoutSerializer,
    OrderItemSerializer,
    OrderSerializer,
)


class CheckoutAPIView(VersioningAPIViewMixin, GenericAPIView):
    permission_classes = [IsAuthenticated]
    version_map = {
        "v1": {
            "serializer_class": CheckoutSerializer,
        },
    }

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderCreationService.create_order(
            user=request.user,
        )
        for item in serializer.validated_data["items"]:
            order_item_serializer = CheckoutItemCreateSerializer(data={
                "order": order.pk,
                "quantity": item["quantity"],
                "product": item["product"].pk,
            })
            order_item_serializer.is_valid(raise_exception=True)
            order_item_serializer.save()
        session = OrderPaymentService.create_checkout_session(
            user=request.user,
            order=order,
            success_url="http://localhost/api/schema/swagger-ui/#/payments/payments_orders_checkout_create",
            cancel_url="http://localhost/api/schema/swagger-ui/#/payments/payments_orders_checkout_create"
        )
        order.payment_link = session["url"]
        serializer = CheckoutResponseSerializer(instance=order)
        return Response(serializer.data)


class OrderViewSet(VersioningAPIViewMixin, ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    filterset_class = OrderFilterSet
    version_map = {
        "v1": {
            "serializer_class": OrderSerializer
        }
    }

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        pk = self.kwargs.get("pk", None)

        if not self.request.user.is_staff:
            if self.action == "retrieve":
                return self.request.user.orders.all()

            if self.action == "order_items":
                return OrderItem.objects.filter(order=pk, order__user=self.request.user)

        if self.action == "order_items":
            return OrderItem.objects.filter(order=pk)

        return super().get_queryset()

    @action(
        methods=["GET"],
        detail=True,
        queryset = OrderItem.objects.all(),
        url_path="items",
        permission_classes=[IsAuthenticated],
        filterset_class=None,
        version_map={
            "v1": {
                "serializer_class": OrderItemSerializer,
            }
        }
    )
    def order_items(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, id=pk)
        self.check_object_permissions(request, order)
        return self.list(request, *args, **kwargs)

class OrderItemViewSet(
    VersioningAPIViewMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    queryset = OrderItem.editable_manager.all()
    permission_classes = [DjangoModelPermissions, IsAdminUser]
    version_map = {
        "v1": {
            "serializer_class": OrderItemSerializer
        }
    }

    def get_permissions(self):
        if self.action == "retrieve":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        if self.action == "retrieve":
            if not self.request.user.is_staff:
                return OrderItem.objects.filter(order__user=self.request.user)

            return OrderItem.objects.all()

        return super().get_queryset()
