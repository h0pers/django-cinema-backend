import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField

from apps.api.payments.orders.models import Order
from apps.core.models import PaymentProviderModel, TimestampModel


class Transaction(TimestampModel, PaymentProviderModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        blank=True,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    amount = MoneyField(
        max_digits=10,
        decimal_places=2,
    )
    paid = models.BooleanField(default=False)

    class Meta(TimestampModel.Meta, PaymentProviderModel.Meta):
        pass

    def __str__(self):
        return _("Transaction ID: %(id)s") % { "id": self.id }
