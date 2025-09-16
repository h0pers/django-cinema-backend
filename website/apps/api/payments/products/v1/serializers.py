from rest_framework import serializers

from apps.api.payments.products.models import Product
from apps.api.payments.subscriptions.v1.serializers import SubscriptionSerializer


class ProductSerializerV1(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
