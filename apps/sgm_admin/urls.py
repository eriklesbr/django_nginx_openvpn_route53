from django.urls import path, include
from rest_framework_nested import routers
from apps.sgm_admin.views import (
    user,
    group
)

app_name = 'apps.sgm_admin'

router = routers.DefaultRouter()

router.register(r'users', user.UserViewSet)
router.register(r'groups', group.GroupViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
]
