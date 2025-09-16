from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.api.custom_user.tasks import update_stripe_customer_task

User = get_user_model()


@receiver(post_save, sender=User)
def update_stripe_customer(instance: User, created: bool, **kwargs):
    if not created:
        stripe_customer_id = instance.stripe_customer_id
        update_stripe_customer_task.delay(stripe_customer_id=stripe_customer_id)
