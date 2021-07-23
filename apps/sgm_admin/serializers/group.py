from django.contrib.auth.models import Group
from rest_framework import serializers


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="apps.sgm_admin:group-detail")
    class Meta:
        model = Group
        fields = ['url', 'name']