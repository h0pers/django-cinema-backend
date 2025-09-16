from rest_framework.routers import DefaultRouter

from apps.api.languages.views import LanguageViewSet

app_name = "languages"

router = DefaultRouter()
router.register("", LanguageViewSet, basename="languages")

urlpatterns = []

urlpatterns += router.urls
