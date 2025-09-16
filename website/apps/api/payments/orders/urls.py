from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.api.payments.orders.views import CheckoutAPIView, OrderItemViewSet, OrderViewSet

app_name = "orders"

router = DefaultRouter()
router.register("", OrderViewSet, basename="orders")
router.register("items", OrderItemViewSet, basename="order-items")

urlpatterns = [
    path("checkout/", CheckoutAPIView.as_view(), name="checkout"),
]

urlpatterns += router.urls
