from rest_framework.routers import DefaultRouter

from .views import UploadViewSet

app_name = "uploads"

router = DefaultRouter()
router.register("", UploadViewSet, basename="uploads")

urlpatterns = []

urlpatterns += router.urls
