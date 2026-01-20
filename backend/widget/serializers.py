from rest_framework import serializers
from .models import WidgetConfig

class WidgetConfigSerializer(serializers.ModelSerializer):
    """Serializer for widget configuration used by the frontend widget."""
    class Meta:
        model = WidgetConfig
        fields = [
            'primary_color',
            'secondary_color',
            'font_family',
            'position',
            'button_text',
            'header_text',
            'description_text',
        ] 
