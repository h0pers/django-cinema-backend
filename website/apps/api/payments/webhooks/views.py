import json

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .handlers.stripe_webhook import StripeWebhookHandler

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

User = get_user_model()

@csrf_exempt
@transaction.atomic
def webhook(request) -> HttpResponse:
    payload = request.body
    try:
        event = stripe.Event.construct_from(
            json.loads(payload), stripe.api_key
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)

    stripe_handler = StripeWebhookHandler(event)
    stripe_handler.handle()

    return HttpResponse(status=200)
