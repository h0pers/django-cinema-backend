from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from djmoney.models.validators import MinMoneyValidator


class PaymentProviderType(models.TextChoices):
    MANUAL = "manual", _("Manual")
    STRIPE = "stripe", _("Stripe")


class PayableModel(models.Model):
    # Basic price of product
    price = MoneyField(
        default_currency=settings.DEFAULT_CURRENCY,
        max_digits=10,
        decimal_places=2,
        validators=[MinMoneyValidator(0)],
    )

    # Discount price doesn't mean price with applied coupon.
    # It means the sale price of the product
    discount_price = MoneyField(
        default_currency=settings.DEFAULT_CURRENCY,
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinMoneyValidator(0)],
    )

    # The Final price of product.
    # Use this field whenever to invoice or calculate.
    final_price = MoneyField(
        max_digits=10,
        decimal_places=2,
        validators=[MinMoneyValidator(0)],
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.final_price = self.discount_price or self.price
        super().save(*args, **kwargs)

    def clean(self):
        if (
            self.discount_price is not None and
            self.discount_price.currency != self.price.currency
        ):
            raise ValidationError("Discount price currency must be the same as price currency")
        if (
            self.discount_price is not None and
            self.discount_price >= self.price
        ):
            raise ValidationError("Discount price must be less than price")


class ExternalPaymentModel(models.Model):
    external_payment_id = models.CharField(
        max_length=255,
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=["external_payment_id"],
                condition=~Q(external_payment_id=''),
                name="unique_%(class)s_external_payment_id"
            )
        ]


class PaymentProviderModel(ExternalPaymentModel):
    payment_provider = models.CharField(
        choices=PaymentProviderType.choices,
        default=PaymentProviderType.MANUAL,
        max_length=20,
        db_index=True,
    )

    class Meta(ExternalPaymentModel.Meta):
        abstract = True

    def clean(self):
        if self.payment_provider != PaymentProviderType.MANUAL and not self.external_payment_id:
            raise ValidationError(_("External payment id is required when payment provider is not manual"))
