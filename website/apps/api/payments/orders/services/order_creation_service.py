from django.contrib.auth.models import AbstractUser

from apps.api.payments.orders.models import Order


class OrderCreationService:
    @staticmethod
    def create_order(
        user: AbstractUser,
        full_name: str = None,
        email: str = None,
    ) -> Order:
        full_name = full_name or user.get_full_name()
        email = email or user.email
        order = Order.objects.create(
            full_name=full_name,
            email=email,
            user=user,
        )
        return order
