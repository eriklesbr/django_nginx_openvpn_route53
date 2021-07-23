from django.urls import path, include
from django.conf import settings
from . import view_api_home_page
from django.conf.urls.static import static
from rest_framework_nested import routers


urlpatterns = [
    # Página inicial (Retorna um HTML com o status da api Ex: "ONLINE".
    # ToDo: Modificar para retornar um JSON)
    path(r'v1/', view_api_home_page.index),
    path(r'v1/admin/', include('apps.sgm_admin.urls', 'admin')),
    path(r'v1/openvpn/', include('apps.sgm_openvpn.urls', 'openvpn')),
    path(r'v1/route53/', include('apps.sgm_route53.urls', 'route53')),
    path(r'v1/nginx/', include('apps.sgm_nginx.urls', 'nginx')),
    path(r'api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
