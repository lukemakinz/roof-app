from django.contrib import admin
from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price_per_m2', 'waste_factor', 'active', 'sort_order']
    list_filter = ['category', 'active']
    list_editable = ['price_per_m2', 'active', 'sort_order']
    search_fields = ['name']
