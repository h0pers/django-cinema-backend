from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import HLSKeyAPIView, VideoViewSet

app_name = "videos"

router = DefaultRouter()
router.register("", VideoViewSet, basename="videos")

urlpatterns = [
    path("<uuid:pk>/hls.key", HLSKeyAPIView.as_view(), name="hls-key"),
]

urlpatterns += router.urls
