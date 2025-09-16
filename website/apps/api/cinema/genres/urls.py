from rest_framework.routers import DefaultRouter

from .views import GenreViewSet

app_name = "genres"

router = DefaultRouter()
router.register('', GenreViewSet, basename='genres')

urlpatterns = []

urlpatterns += router.urls
