from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.api.custom_user.models import UserSubscription
from apps.api.payments.orders.models import Order, OrderItem
from apps.api.payments.products.models import Product

User = get_user_model()


class CheckoutItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.public.all())
    quantity = serializers.IntegerField(
        validators=[
            MinValueValidator(settings.CHECKOUT_SETTINGS["MIN_QUANTITY"]),
            MaxValueValidator(settings.CHECKOUT_SETTINGS["MAX_QUANTITY"])
        ]
    )

    class Meta:
        model = OrderItem
        fields = [
            "quantity",
            "product",
        ]

    def validate_product(self, value):
        if not value.in_stock:
            raise ValidationError(_("Product %(product)s out of stock") % {
                "product": str(value)
            })
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        product = attrs["product"]
        quantity = attrs["quantity"]

        if product.is_subscription and quantity != 1:
            raise ValidationError({"quantity": _("Subscription product quantity must equal 1")})

        if product.in_stock and product.stock is not None and quantity > product.stock:
            raise ValidationError({
                "quantity": _("Product %(product)s has %(amount)s left") % {
                    "product": str(product),
                    "amount": product.stock,
                }
            })
        return attrs


class CheckoutItemCreateSerializer(CheckoutItemSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "order",
            "quantity",
            "product",
        ]


class CheckoutSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    items = CheckoutItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "user",
            "items",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        items = attrs["items"]
        user = attrs["user"]

        subscription_ids = [
            item["product"].subscription_id for item in items
            if item["product"].is_subscription
        ]
        active_subscriptions = (
            UserSubscription.objects
            .filter(user=user, subscription_id__in=subscription_ids)
            .active()
        )

        if active_subscriptions.exists():
            raise ValidationError({"items": _("User already subscribed to subscription")})

        return attrs

    def validate_items(self, items):
        if not items:
            raise ValidationError(_("Cannot be empty"))

        subscriptions_count = []
        product_ids = []

        for idx, item in enumerate(items):
            product = item["product"]
            product_ids.append(product.id)

            if product.is_subscription:
                subscriptions_count.append(idx)

            if len(subscriptions_count) > 1:
                raise ValidationError(_("More than one subscription in items"))

        if len(set(product_ids)) != len(product_ids):
            raise ValidationError(_("Duplicate product in items"))

        return items


class CheckoutResponseSerializer(serializers.ModelSerializer):
    payment_link = serializers.URLField(read_only=True)
    items = CheckoutItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "email",
            "full_name",
            "payment_link",
            "user",
            "items",
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    total_price = serializers.DecimalField(
        source="total_price.amount",
        max_digits=10, decimal_places=2,
        read_only=True, allow_null=True,
    )
    total_price_currency = serializers.CharField(
        source="total_price.currency.code",
        read_only=True, allow_null=True,
    )
    total_items = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
