from rest_framework.routers import DefaultRouter

from .views import AudioTrackViewSet

app_name = "audio_tracks"

router = DefaultRouter()
router.register("", AudioTrackViewSet, basename="audio_tracks")

urlpatterns = []

urlpatterns += router.urls
