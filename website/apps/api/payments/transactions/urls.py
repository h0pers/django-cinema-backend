from rest_framework.routers import DefaultRouter

from apps.api.payments.transactions.views import TransactionViewSet

router = DefaultRouter()
router.register('', TransactionViewSet, basename='transactions')

urlpatterns = []

urlpatterns += router.urls
