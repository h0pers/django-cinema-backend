from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, transaction
from djmoney.money import Money

from apps.api.payments.orders.models import Order
from apps.api.payments.transactions.exceptions import TransactionAlreadyExists
from apps.api.payments.transactions.models import Transaction
from apps.core.models import PaymentProviderType


class TransactionManagerService:
    @staticmethod
    @transaction.atomic
    def create_transaction(
        order: Order,
        amount: Money,
        payment_provider: PaymentProviderType = PaymentProviderType.MANUAL,
        paid: bool = False,
        external_payment_id: str = '',
        customer: AbstractUser = None,
    ):
        try:
            Transaction.objects.create(
                order=order,
                amount=amount,
                payment_provider=payment_provider,
                external_payment_id=external_payment_id,
                customer=customer,
                paid=paid,
            )
        except IntegrityError as e:
            raise TransactionAlreadyExists("Transaction with provided payment_id already exists") from e

    @staticmethod
    def paid(obj: Transaction):
        obj.paid = True
        obj.save()
