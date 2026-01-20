from django.contrib import admin
from .models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['number', 'client_name', 'status', 'roof_type', 'total_gross', 'created_at']
    list_filter = ['status', 'roof_type', 'created_at']
    search_fields = ['number', 'client_name', 'client_email']
    readonly_fields = ['number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Meta', {
            'fields': ('number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Klient', {
            'fields': ('client_name', 'client_email', 'client_phone', 'client_address')
        }),
        ('Dach', {
            'fields': ('roof_type', 'plan_area', 'real_area', 'pitch_angle', 'dimensions', 'obstacles')
        }),
        ('AI', {
            'fields': ('original_image', 'processed_image', 'ai_extracted_data', 'ai_confidence', 'ai_processed'),
            'classes': ('collapse',)
        }),
        ('Materiały i koszty', {
            'fields': ('material', 'materials_breakdown', 'margin_percent', 'vat_rate', 'total_net', 'total_gross')
        }),
        ('PDF', {
            'fields': ('pdf_file',)
        }),
    )
