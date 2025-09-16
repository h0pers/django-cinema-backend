from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.core.models import DescriptiveModel, PayableModel, TimestampModel


class ProductTypeModel(models.Model):
    class Type(models.TextChoices):
        PRODUCT = 'product', _('Product')
        SUBSCRIPTION = 'subscription', _('Subscription')

    type = models.CharField(choices=Type.choices, max_length=20, editable=False)

    class Meta:
        abstract = True

    @property
    def is_subscription(self) -> bool:
        return self.type == self.Type.SUBSCRIPTION

    @property
    def is_product(self) -> bool:
        return self.type == self.Type.PRODUCT


class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            ~Q(status=self.model.Status.DRAFT),
        )


class Product(ProductTypeModel, DescriptiveModel, PayableModel, TimestampModel):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    # SEO Optimization, not unique, use primary key in URLs
    # E.g. <int:pk>/<slug:slug>
    slug = models.SlugField(max_length=255)

    status = models.CharField(choices=Status.choices, max_length=20, default=Status.DRAFT)

    # Null means unlimited amount, while zero is out of stock
    stock = models.PositiveIntegerField(null=True, blank=True)

    # If the subscription field is defined to product,
    # subscription will be applied to user on success purchase
    subscription = models.OneToOneField(
        "Subscription",
        on_delete=models.PROTECT,
        related_name='product',
        blank=True,
        null=True,
    )

    objects = models.Manager()
    public = ProductManager()

    class Meta(ProductTypeModel.Meta, DescriptiveModel.Meta, PayableModel.Meta, TimestampModel.Meta):
        pass

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.type = self._calculate_type()
        super().save(*args, **kwargs)

    @property
    def in_stock(self) -> bool:
        return self.stock is None or self.stock > 0

    @property
    def draft(self) -> bool:
        return self.status == self.Status.DRAFT

    @property
    def published(self) -> bool:
        return self.status == self.Status.PUBLISHED

    def _calculate_type(self) -> ProductTypeModel.Type:
        return self.Type.SUBSCRIPTION if self.subscription_id else self.Type.PRODUCT
