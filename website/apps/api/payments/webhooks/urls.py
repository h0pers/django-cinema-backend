from django.urls import path

from .views import webhook

app_name = "webhooks"

urlpatterns = [
    path("", webhook, name="stripe"),
]
