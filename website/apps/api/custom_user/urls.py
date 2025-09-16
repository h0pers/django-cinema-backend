from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.custom_user.views import GroupViewSet, PermissionViewSet, UserSubscriptionViewSet, UserViewSet

app_name = "users"

router = DefaultRouter()
router.register("users/subscriptions", UserSubscriptionViewSet, basename="user-subscriptions")
router.register("users", UserViewSet, basename="users")
router.register("permissions", PermissionViewSet, basename="permissions")
router.register("groups", GroupViewSet, basename="groups")

urlpatterns = [
    path("", include("dj_rest_auth.urls")),
    path("registration/", include('dj_rest_auth.registration.urls')),
]

urlpatterns += router.urls

