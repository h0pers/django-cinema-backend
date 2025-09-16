from rest_framework.routers import DefaultRouter

from .views import TitleCrewViewSet, TitleViewSet

app_name = "titles"

router = DefaultRouter()
router.register("crew", TitleCrewViewSet, basename="crew")
router.register("", TitleViewSet, basename="titles")

urlpatterns = []

urlpatterns += router.urls
