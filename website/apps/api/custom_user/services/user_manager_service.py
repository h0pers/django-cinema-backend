from django.contrib.auth.models import AbstractUser


class UserManagerService:
    @staticmethod
    def set_stripe_customer_id(user: AbstractUser, stripe_customer_id: str):
        user.stripe_customer_id = stripe_customer_id
        user.save()

    @staticmethod
    def remove_stripe_customer_id(user: AbstractUser):
        user.stripe_customer_id = ''
        user.save()
