import stripe
from django.contrib.auth.models import AbstractUser


class StripeCustomerService:
    @staticmethod
    def create_customer(user: AbstractUser):
        customer = stripe.Customer.create(
            name=user.get_full_name(),
            email=user.email,
            metadata={
                'user_id': user.id,
            }
        )
        user.stripe_customer_id = customer.id
        user.save()

    @staticmethod
    def update_customer(user: AbstractUser):
        stripe_customer_id = user.stripe_customer_id
        full_name = user.get_full_name()
        stripe.Customer.modify(
            stripe_customer_id,
            name=full_name,
            email=user.email,
        )

    @staticmethod
    def clear_customer(user: AbstractUser):
        user.stripe_customer_id = ""
        user.save()
