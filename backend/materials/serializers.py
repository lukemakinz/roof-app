from rest_framework import serializers
from .models import Material


class MaterialSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'name', 'category', 'category_display', 'description',
            'price_per_m2', 'waste_factor', 'config', 'active', 'sort_order'
        ]
