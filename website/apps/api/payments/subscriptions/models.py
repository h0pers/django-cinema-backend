from datetime import datetime

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from utils.intervals import Interval, interval_to_relativedelta

from apps.api.custom_user.models import CustomGroup
from apps.api.payments.products.models import Product
from apps.core.models import DescriptiveModel


class SubscriptionManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            product__status=Product.Status.PUBLISHED,
        )


class Subscription(DescriptiveModel):
    trial_interval_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    trial_interval = models.CharField(
        choices=Interval.choices,
        max_length=20,
        blank=True
    )
    billing_interval_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    billing_interval = models.CharField(
        choices=Interval.choices,
        max_length=20,
    )
    group = models.OneToOneField(
        CustomGroup,
        on_delete=models.PROTECT,
        related_name='subscription',
    )

    objects = models.Manager()
    public = SubscriptionManager()

    @property
    def has_trial(self):
        return bool(self.trial_interval)

    @property
    def trial_end(self) -> datetime | None:
        now = timezone.now()
        delta = interval_to_relativedelta(self.trial_interval, self.trial_interval_count)
        return now + delta if self.has_trial else None

    @property
    def trial_days(self) -> int | None:
        trial_end_date = self.trial_end.date()
        now = timezone.now().date()
        return (trial_end_date - now).days
