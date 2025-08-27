from django.contrib import admin
from .models import DistributionCenter


@admin.register(DistributionCenter)
class DistributionCenterAdmin(admin.ModelAdmin):
    list_display = ['created', 'modified', 'is_active', 'name', 'url', 'description', 'region', 'status', 'balance']
    search_fields = ['name', 'created', 'is_active', 'url', 'region']