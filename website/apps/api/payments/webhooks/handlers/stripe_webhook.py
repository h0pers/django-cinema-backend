import logging
from datetime import UTC, datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from djmoney.money import Money
from utils.money import cents_to_money

from apps.api.custom_user.exceptions import AlreadySubscribedError
from apps.api.custom_user.models import UserSubscription
from apps.api.custom_user.services.stripe_customer_service import StripeCustomerService
from apps.api.custom_user.services.user_subscription_service import UserSubscriptionService
from apps.api.payments.orders.models import Order
from apps.api.payments.orders.services.order_payment_service import OrderPaymentService
from apps.api.payments.subscriptions.models import Subscription
from apps.api.payments.transactions.models import Transaction
from apps.api.payments.transactions.services.transaction_manager_service import TransactionManagerService
from apps.core.models import PaymentProviderType

from .base import BaseHandler

User = get_user_model()


class StripeWebhookHandler(BaseHandler):
    def __init__(self, event, *args, **kwargs):
        # Stripe webhook data
        self.data = event.data.object
        # Key pair of event type and defined handler
        self.event_handlers = {
            "checkout.session.completed": self.checkout_completed,
            "customer.deleted": self.customer_deleted,
            "invoice.created": self.invoice_created,
            "invoice.paid": self.invoice_paid,
            "customer.subscription.created": self.customer_subscription_created,
            "customer.subscription.updated": self.customer_subscription_updated,
            "customer.subscription.deleted": self.customer_subscription_deleted,
        }
        super().__init__(event, *args, **kwargs)

    def handle(self, *args, **kwargs):
        self.event_handlers.get(self.event.type, lambda: None)()

    def checkout_completed(self):
        # client_reference_id by default, is order id
        order_id = self.data.client_reference_id
        try:
            order = Order.objects.get(id=order_id)
        except ObjectDoesNotExist:
            logging.error(
                "Stripe Checkout: Couldn't find order with reference ID: %s in the database",
                order_id
            )
            return

        OrderPaymentService.order_paid(order)

    def invoice_paid(self):
        try:
            transaction = Transaction.objects.get(
                payment_provider=PaymentProviderType.STRIPE,
                external_payment_id=self.data.id,
            )
        except ObjectDoesNotExist:
            logging.error(
                "Invoice can not be set as paid, transaction with %s doesn't exists in database",
                self.data.id,
            )
            return

        if transaction.paid:
            # If a transaction was paid by one transaction, it
            # sets paid in invoice_created, avoid double queries in DB
            return

        TransactionManagerService.paid(transaction)

    def invoice_created(self):
        order_id = self.data.lines.data[0].metadata["order_id"]
        try:
            customer = User.objects.get(stripe_customer_id=self.data.customer)
        except ObjectDoesNotExist:
            logging.error("User with %s stripe customer id doesn't exist", self.data.customer)
            return
        try:
            order = Order.objects.get(id=order_id)
        except ObjectDoesNotExist:
            logging.error("Transaction can not be created, order with %s doesn't exists in database", order_id)
            return

        total = cents_to_money(self.data.total)
        total_money = Money(total, self.data.currency)

        TransactionManagerService.create_transaction(
            order=order,
            amount=total_money,
            external_payment_id=self.data.id,
            payment_provider=PaymentProviderType.STRIPE,
            customer=customer,
        )

    def customer_subscription_created(self):
        # UTC Timezone
        expire_date = datetime.fromtimestamp(self.data.current_period_end, UTC)
        subscription_id = self.data.metadata.subscription_id
        order_id = self.data.metadata.order_id
        try:
            subscription = Subscription.objects.get(id=subscription_id)
        except ObjectDoesNotExist:
            logging.error(
                "Couldn't sign up user to subscription, no subscription with reference ID: %s in the database",
                subscription_id
            )
            return
        try:
            order = Order.objects.get(id=order_id)
        except ObjectDoesNotExist:
            logging.error(
                "Couldn't sign up user to subscription, no order with reference ID: %s in the database", order_id
            )
            return
        try:
            UserSubscriptionService.subscribe(
                user=order.user,
                subscription=subscription,
                expire_date=expire_date,
                payment_provider=PaymentProviderType.STRIPE,
                external_payment_id=self.data.id,
                order=order,
            )
        except AlreadySubscribedError:
            logging.error(
                "Couldn't sign up user to subscription, already subscribed to subscription with reference ID: %s",
                subscription_id
            )

    def customer_subscription_updated(self):
        subscription_id = self.data.id
        # UTC Timezone
        expire_date = datetime.fromtimestamp(self.data.current_period_end, UTC)
        try:
            user_subscription = UserSubscription.objects.get(
                payment_provider=PaymentProviderType.STRIPE,
                external_payment_id=subscription_id,
            )
        except ObjectDoesNotExist:
            logging.error(
                "User subscription with %s payment id doesn't exists and can not be extended", subscription_id
            )
            return

        user_subscription_expire_date = user_subscription.expires.astimezone(UTC)

        if user_subscription_expire_date == expire_date:
            return

        UserSubscriptionService.extend(
            user_subscription=user_subscription,
            expire_date=expire_date,
            # Subscription already updated in Stripe merchant, we need to change
            # Information in the database only
            merchant_update=False,
        )

    def customer_subscription_deleted(self):
        subscription_id = self.data.id
        try:
            user_subscription = UserSubscription.objects.get(
                payment_provider=PaymentProviderType.STRIPE,
                external_payment_id=subscription_id,
            )
        except ObjectDoesNotExist:
            logging.info(
                "User subscription with %s payment id doesn't exists and can not be canceled", subscription_id
            )
            return

        # Already updated in merchant
        UserSubscriptionService.cancel(user_subscription, merchant_update=False)

    def customer_deleted(self):
        try:
            user = User.objects.get(stripe_customer_id=self.data.id)
            StripeCustomerService.clear_customer(user)
        except ObjectDoesNotExist:
            logging.info(
                "User subscription with %s payment id doesn't exists and can not be extended", self.data.id
            )
            return
