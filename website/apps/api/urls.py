from django.urls import include, path

app_name = "api"

urlpatterns = [
    path("auth/", include("apps.api.custom_user.urls")),
    path("languages/", include("apps.api.languages.urls")),
    path("payments/", include("apps.api.payments.urls")),
    path("cinema/", include("apps.api.cinema.urls")),
    path("uploads/", include("apps.api.uploads.urls")),
]
