from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from apps.api.payments.transactions.models import Transaction
from apps.core.models import PaymentProviderType


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        exclude = [
            "external_payment_id",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        payment_provider = attrs.get("payment_provider", None)
        external_payment_id = attrs.get("external_payment_id", None)

        if payment_provider != PaymentProviderType.MANUAL and not external_payment_id:
            raise ValidationError({
                "payment_provider": _("External payment id is required when payment provider is not manual")
            })

        return attrs

class TransactionStaffSerializer(TransactionSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
