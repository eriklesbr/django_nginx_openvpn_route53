from django.urls import path, include
from rest_framework_nested import routers
from apps.sgm_openvpn.views.openvpn import VPNViewSet


app_name = 'apps.sgm_openvpn'

router = routers.DefaultRouter()

router.register(r'vpns', VPNViewSet, basename='vpn')

urlpatterns = [
    path(r'', include(router.urls)),
]
