from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from djmoney.money import Money

from apps.api.payments.products.models import Product, ProductTypeModel
from apps.core.models import DescriptiveModel, PayableModel, TimestampModel


class Order(TimestampModel):
    class Status(models.TextChoices):
        CANCELED = 'canceled'
        REFUNDED = 'refunded'
        PENDING = 'pending'
        COMPLETED = 'completed'

    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    status = models.CharField(choices=Status.choices, default=Status.PENDING, max_length=20)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return _("Order ID: %(id)s") % { "id": self.id}

    @property
    def total_price(self) -> Money | None:
        """
        Returns the total price of the order
        Current functionality doesn't support multi currencies.
        Rewrite the logic if needed
        """
        total: Decimal | None = self.items.aggregate(total=Sum("final_price")).get("total", None)

        if total is None:
            return None

        return Money(total, settings.DEFAULT_CURRENCY)


class EditableOrderItemManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            ~Q(order__status=Order.Status.COMPLETED),
            order__paid=False,
        )


class OrderItem(ProductTypeModel, DescriptiveModel, PayableModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    # Always use DescriptiveModel fields to display product
    # These fields are product snapshot on a moment of purchase
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
    )

    objects = models.Manager()
    editable_manager = EditableOrderItemManager()

    class Meta(ProductTypeModel.Meta, DescriptiveModel.Meta, PayableModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_order_item',
            )
        ]

    @property
    def total_price(self) -> Money | None:
        # This field is final_price multiplied by quantity
        # Use this field as total price of whole order item
        # Don't mix with final_price, which represents the final
        # price of one product
        return self.final_price * self.quantity if self.pk else None

    def clean(self):
        if (
            not self.order.paid and
            not self.product.in_stock
        ):
            raise ValidationError(_("Product out of stock"))
        super().clean()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.name = self.product.name
            self.description = self.product.description
            self.type = self.product.type
            self.price = self.product.price
            self.discount_price = self.product.discount_price
            # Final price represents final price of ONE product
            # and doesn't include quantity calculations
            self.final_price = self.product.final_price
        super().save(*args, **kwargs)
