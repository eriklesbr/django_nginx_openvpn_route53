from django.urls import path, include
from rest_framework_nested import routers
from apps.sgm_route53.views.route53 import HostedZoneViewSet, RecordSetViewSet


app_name = 'apps.sgm_route53'

router = routers.DefaultRouter()

router.register(r'hosted_zones', HostedZoneViewSet, basename='hosted_zones')

record_set_router = routers.NestedDefaultRouter(router, r'hosted_zones', lookup='hosted_zone')
record_set_router.register(r'record_sets', RecordSetViewSet, basename='record_sets')

urlpatterns = [
    path(r'', include(router.urls)),
    path(r'', include(record_set_router.urls))
]
