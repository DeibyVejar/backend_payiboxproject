from rest_framework.routers import DefaultRouter
from .views import OrderViewSet

router = DefaultRouter()
# El prefijo vacío '' es correcto aquí porque 'api/orders/'
# ya viene desde el archivo principal (config/urls.py)
router.register(r'', OrderViewSet, basename='order')

urlpatterns = router.urls
