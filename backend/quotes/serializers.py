from rest_framework import serializers
from .models import Quote
from materials.serializers import MaterialSerializer


class QuoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for quote list view."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    roof_type_display = serializers.CharField(source='get_roof_type_display', read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            'id', 'number', 'client_name', 'status', 'status_display',
            'roof_type', 'roof_type_display', 'real_area', 'total_gross',
            'created_at', 'updated_at'
        ]


class QuoteDetailSerializer(serializers.ModelSerializer):
    """Full serializer for quote detail/edit views."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    roof_type_display = serializers.CharField(source='get_roof_type_display', read_only=True)
    material_detail = MaterialSerializer(source='material', read_only=True)
    original_image_url = serializers.SerializerMethodField()
    processed_image_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Quote
        fields = [
            'id', 'number', 'status', 'status_display',
            # Client
            'client_name', 'client_email', 'client_phone', 'client_address',
            # Roof
            'roof_type', 'roof_type_display', 'plan_area', 'real_area', 'pitch_angle',
            'dimensions', 'obstacles',
            # AI
            'original_image_url', 'processed_image_url',
            'ai_extracted_data', 'ai_confidence', 'ai_processed', 'ai_processing',
            # Material
            'material', 'material_detail', 'materials_breakdown',
            # Financials
            'margin_percent', 'vat_rate', 'total_net', 'total_gross',
            # PDF
            'pdf_url',
            # Timestamps
            'created_at', 'updated_at', 'sent_at'
        ]
        read_only_fields = ['id', 'number', 'ai_processed', 'ai_processing', 'created_at', 'updated_at']
    
    def get_original_image_url(self, obj):
        if obj.original_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.original_image.url) if request else obj.original_image.url
        return None
    
    def get_processed_image_url(self, obj):
        if obj.processed_image:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.processed_image.url) if request else obj.processed_image.url
        return None
    
    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.pdf_file.url) if request else obj.pdf_file.url
        return None


class QuoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new quotes."""
    class Meta:
        model = Quote
        fields = ['id', 'number', 'client_name', 'client_email', 'client_phone', 'client_address']
        read_only_fields = ['id', 'number']


class QuoteUploadSerializer(serializers.Serializer):
    """Serializer for image upload."""
    image = serializers.ImageField()


class QuoteDimensionsSerializer(serializers.Serializer):
    """Serializer for updating dimensions."""
    length = serializers.FloatField(min_value=2, max_value=50)
    width = serializers.FloatField(min_value=2, max_value=30)
    pitch_angle = serializers.IntegerField(min_value=3, max_value=70, required=False)
    roof_type = serializers.ChoiceField(choices=Quote.ROOF_TYPES, required=False)


class QuoteCalculateSerializer(serializers.Serializer):
    """Serializer for calculation request."""
    material_id = serializers.IntegerField()
    margin_percent = serializers.IntegerField(min_value=0, max_value=100, required=False, default=35)
