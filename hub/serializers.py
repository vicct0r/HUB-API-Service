from rest_framework import serializers
from .models import DistributionCenter

class CdSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionCenter
        fields = ['created', 'modified', 'is_active', 'name', 'description', 'url', 'ip', 'region', 'status', 'balance', 'slug']
        extra_kwargs = {
            'created': {'read_only': True},
            'modified': {'read_only': True},
            'is_active': {'read_only': True},
            'slug': {'read_only': True},
            'balance': {'read_only': True},
            'url': {'read_only': True}
        }


class CdInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionCenter
        fields = ['name', 'status', 'balance']