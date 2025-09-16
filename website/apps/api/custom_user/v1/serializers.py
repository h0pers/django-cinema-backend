from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import ModelSerializer

from apps.api.custom_user.models import CustomGroup, UserSubscription
from apps.api.payments.subscriptions.models import Subscription
from apps.api.payments.subscriptions.v1.serializers import SubscriptionSerializer
from apps.core.models import PaymentProviderType

User = get_user_model()


class UserSubscriptionSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)
    subscription_id = serializers.PrimaryKeyRelatedField(
        source="subscription",
        queryset=Subscription.objects.all(),
        write_only=True,
    )
    active = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        exclude = [
            "external_payment_id",
        ]

    def validate_payment_provider(self, value):
        if value != PaymentProviderType.MANUAL:
            raise ValidationError(_("Payment provider must be manual"))
        return value

    def get_active(self, obj) -> bool:
        return obj.active


class UserSubscriptionStaffSerializer(UserSubscriptionSerializer):
    class Meta:
        model = UserSubscription
        fields = "__all__"


class BillingUserSubscriptionSerializer(serializers.Serializer):
    next_billing_date = serializers.DateTimeField(
        validators=[
        MinValueValidator(
            limit_value=timezone.now,
            message=_("Expiration date must be in the future")
        )
    ])


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        exclude = [
            "content_type",
        ]


class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permissions_ids = PrimaryKeyRelatedField(
        source="permissions",
        queryset=Permission.objects.all(),
        many=True,
        write_only=True,
    )

    class Meta:
        model = CustomGroup
        fields = "__all__"


class UserGroupSerializer(ModelSerializer):
    class Meta:
        model = CustomGroup
        fields = [
            "id",
            "name",
        ]


class UserSerializer(ModelSerializer):
    groups = UserGroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        exclude = [
            "password",
        ]


class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
