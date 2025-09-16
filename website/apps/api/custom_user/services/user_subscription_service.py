from datetime import UTC, datetime

import stripe
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.api.custom_user.exceptions import AlreadySubscribedError, SubscriptionDisabledError
from apps.api.custom_user.models import UserSubscription
from apps.api.payments.orders.models import Order
from apps.api.payments.subscriptions.models import Subscription
from apps.core.models import PaymentProviderType


class UserSubscriptionService:
    @staticmethod
    @transaction.atomic
    def subscribe(
        user: AbstractUser,
        subscription: Subscription,
        expire_date: datetime,
        payment_provider: PaymentProviderType = PaymentProviderType.MANUAL,
        external_payment_id: str = '',
        order: Order = None,
    ):
        """
        Subscribe to user subscription
        """
        expire_date = timezone.localtime(expire_date)
        try:
            UserSubscription.objects.create(
                user=user,
                subscription=subscription,
                expires=expire_date,
                payment_provider=payment_provider,
                external_payment_id=external_payment_id,
                order=order,
            )
            user.groups.add(subscription.group)

        except IntegrityError as e:
            # User already subscribed, use extend method
            raise AlreadySubscribedError("User already subscribed to the subscription") from e

    @staticmethod
    @transaction.atomic
    def extend(user_subscription: UserSubscription, expire_date: datetime, merchant_update: bool = True):
        """
        Extending the current subscription in the database and setting the next billing date
        """
        if user_subscription.disabled:
            raise SubscriptionDisabledError("User subscription is disabled")

        timestamp = int(expire_date.astimezone(UTC).timestamp())
        user_subscription.expires = expire_date
        user_subscription.save()

        if merchant_update:
            if user_subscription.payment_provider == PaymentProviderType.STRIPE:
                stripe.Subscription.modify(
                    user_subscription.external_payment_id,
                    trial_end=timestamp,
                    proration_behavior="none",
                )

    @staticmethod
    @transaction.atomic
    def cancel(user_subscription: UserSubscription, merchant_update: bool = True):
        user_subscription.canceled = True
        user_subscription.canceled_at = timezone.now()
        user_subscription.save()

        if merchant_update:
            if user_subscription.payment_provider == PaymentProviderType.STRIPE:
                stripe.Subscription.cancel(user_subscription.external_payment_id)

    @classmethod
    @transaction.atomic
    def disable(cls, user_subscription: UserSubscription, merchant_update: bool = True):
        user_subscription.disabled = True
        user_subscription.disabled_at = timezone.now()
        if not user_subscription.canceled:
            cls.cancel(user_subscription, merchant_update)
        user_subscription.save()
        user_subscription.user.groups.remove(user_subscription.subscription.group)
