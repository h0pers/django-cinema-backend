import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from apps.api.custom_user.services.stripe_customer_service import StripeCustomerService

User = get_user_model()


@shared_task(bind=True, max_retries=5, default_retry_delay=60 * 5)
def update_stripe_customer_task(self, stripe_customer_id: str):
    try:
        user = User.objects.get(stripe_customer_id=stripe_customer_id)
    except ObjectDoesNotExist:
        logging.error(
            "User with stripe_customer_id=%s does not exist in database",
            stripe_customer_id,
        )
        return

    try:
        StripeCustomerService.update_customer(user)
    except Exception as exc:
        raise self.retry(exc=exc) from exc
