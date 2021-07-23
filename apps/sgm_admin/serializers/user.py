from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="apps.sgm_admin:user-detail")
    groups = serializers.HyperlinkedIdentityField(view_name="apps.sgm_admin:group-detail")
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']
