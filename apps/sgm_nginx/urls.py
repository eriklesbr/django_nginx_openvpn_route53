from django.urls import path, include
from rest_framework_nested import routers
from apps.sgm_nginx.views.nginx import ConfigViewSet


app_name = 'apps.sgm_nginx'

router = routers.DefaultRouter()
router.register(r'configs', ConfigViewSet, basename='config')


urlpatterns = [
    path(r'', include(router.urls))
]
