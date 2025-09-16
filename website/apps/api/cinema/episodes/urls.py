from rest_framework.routers import DefaultRouter

from .views import EpisodeViewSet

app_name = "episodes"

router = DefaultRouter()
router.register("", EpisodeViewSet, basename="episodes")

urlpatterns = []

urlpatterns += router.urls
