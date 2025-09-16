from django.urls import include, path

app_name = "payments"

urlpatterns = [
    path("webhook/", include("apps.api.payments.webhooks.urls")),
    path("orders/", include("apps.api.payments.orders.urls")),
    path("transactions/", include("apps.api.payments.transactions.urls")),
    path("products/", include("apps.api.payments.products.urls")),
    path("subscriptions/", include("apps.api.payments.subscriptions.urls")),
]
