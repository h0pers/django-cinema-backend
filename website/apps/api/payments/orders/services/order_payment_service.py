from decimal import Decimal

import stripe
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import TextChoices
from stripe.checkout import Session

from apps.api.custom_user.services.stripe_customer_service import StripeCustomerService
from apps.api.payments.orders.models import Order, OrderItem


class StripeSessionMode(TextChoices):
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"


class OrderPaymentService:
    @classmethod
    @transaction.atomic
    def create_checkout_session(
        cls,
        user: AbstractUser,
        order: Order,
        success_url: str = None,
        cancel_url: str = None,
    ) -> Session:
        session_mode = cls._calculate_session_mode(order)
        session_data = {
            'mode': session_mode,
            'client_reference_id': order.id,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'line_items': [],
            'metadata': {},
            'subscription_data': {},
        }

        if not user.stripe_customer:
            # Initializing customer stripe customer creation.
            # If a user already has a stripe account, we update information about user
            # in user save method
            StripeCustomerService.create_customer(user)

        session_data['customer'] = user.stripe_customer_id

        for item in order.items.all():
            session_data['line_items'].append({
                'price_data': {
                    'unit_amount': int(item.final_price.amount * Decimal('100')),
                    'currency': item.final_price.currency,
                    'product_data': {
                        'name': item.name,
                        'description': item.description or None,
                        'metadata': {
                            'product_id': item.product_id,
                        }
                    },
                },
                'quantity': item.quantity,
            })
            if item.type == OrderItem.Type.SUBSCRIPTION:
                session_data['line_items'][-1]['price_data']['recurring'] = {
                    'interval': item.product.subscription.billing_interval,
                    'interval_count': item.product.subscription.billing_interval_count,
                }
                session_data["subscription_data"]["metadata"] = {
                    "order_id": order.id,
                    "subscription_id": item.product.subscription_id,
                }
                if item.product.subscription.has_trial:
                    trial_period_days = item.product.subscription.trial_days
                    session_data["subscription_data"]["trial_period_days"] = trial_period_days

        session = stripe.checkout.Session.create(**session_data)
        return session

    @classmethod
    def _calculate_session_mode(cls, order: Order) -> StripeSessionMode:
        return (
            StripeSessionMode.SUBSCRIPTION if
            order.items.filter(type=OrderItem.Type.SUBSCRIPTION).exists() else
            StripeSessionMode.PAYMENT
        )

    @classmethod
    def order_paid(cls, order: Order):
        order.paid = True
        order.save()

    @classmethod
    def order_completed(cls, order: Order):
        order.status = Order.Status.COMPLETED
        order.save()
