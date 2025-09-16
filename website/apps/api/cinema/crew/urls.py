from rest_framework.routers import DefaultRouter

from .views import CrewMemberViewSet

app_name = "crew"

router = DefaultRouter()
router.register("", CrewMemberViewSet, basename="crew")

urlpatterns = []

urlpatterns += router.urls
