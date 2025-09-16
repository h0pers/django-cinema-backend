from rest_framework.routers import DefaultRouter

from .views import SeasonViewSet

app_name = "seasons"

router = DefaultRouter()
router.register("", SeasonViewSet, basename="seasons")

urlpatterns = []

urlpatterns += router.urls
