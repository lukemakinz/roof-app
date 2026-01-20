from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin configuration for Lead model."""

    list_display = [
        'public_uuid_short',
        'email',
        'phone',
        'status_badge',
        'roof_type',
        'roof_area',
        'estimated_price_display',
        'created_at',
        'has_pdf',
    ]
    list_filter = [
        'status',
        'roof_type',
        'created_at',
    ]
    search_fields = [
        'email',
        'phone',
        'public_uuid',
    ]
    readonly_fields = [
        'public_uuid',
        'created_at',
        'updated_at',
        'processing_started_at',
        'processing_completed_at',
        'celery_task_id',
        'ai_raw_response',
        'uploaded_file_preview',
        'result_pdf_link',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Dane kontaktowe', {
            'fields': ('email', 'phone', 'public_uuid')
        }),
        ('Status', {
            'fields': ('status', 'processing_error')
        }),
        ('Przesłany plik', {
            'fields': ('uploaded_file', 'uploaded_file_preview', 'file_type')
        }),
        ('Wyniki analizy AI', {
            'fields': (
                'roof_type',
                'pitch_angle',
                'roof_area',
                'dimensions',
                'roof_elements',
                'ai_confidence',
                'ai_warnings',
            )
        }),
        ('Wycena', {
            'fields': ('estimated_price_min', 'result_pdf', 'result_pdf_link')
        }),
        ('Notatki handlowca', {
            'fields': ('notes', 'contacted_at', 'contacted_by'),
            'classes': ('collapse',)
        }),
        ('Dane techniczne', {
            'fields': (
                'celery_task_id',
                'ai_raw_response',
                'created_at',
                'updated_at',
                'processing_started_at',
                'processing_completed_at',
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_contacted', 'reprocess_leads']

    def public_uuid_short(self, obj):
        """Display shortened UUID."""
        return str(obj.public_uuid)[:8] + '...'
    public_uuid_short.short_description = 'UUID'

    def status_badge(self, obj):
        """Display status with colored badge."""
        colors = {
            'pending': '#f6ad55',
            'processing': '#63b3ed',
            'completed': '#68d391',
            'failed': '#fc8181',
            'contacted': '#b794f4',
            'converted': '#48bb78',
        }
        color = colors.get(obj.status, '#a0aec0')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def estimated_price_display(self, obj):
        """Display price in PLN format."""
        if obj.estimated_price_min:
            return f"{obj.estimated_price_min:,.0f} PLN"
        return '-'
    estimated_price_display.short_description = 'Cena od'

    def has_pdf(self, obj):
        """Display if PDF is available."""
        if obj.result_pdf:
            return format_html(
                '<span style="color: green;">✓</span>'
            )
        return format_html(
            '<span style="color: gray;">-</span>'
        )
    has_pdf.short_description = 'PDF'

    def uploaded_file_preview(self, obj):
        """Display uploaded file preview or link."""
        if obj.uploaded_file:
            file_url = obj.uploaded_file.url
            if obj.file_type in ['jpg', 'png']:
                return format_html(
                    '<img src="{}" style="max-width: 400px; max-height: 300px;" />',
                    file_url
                )
            else:
                return format_html(
                    '<a href="{}" target="_blank">Pobierz plik</a>',
                    file_url
                )
        return '-'
    uploaded_file_preview.short_description = 'Podgląd pliku'

    def result_pdf_link(self, obj):
        """Display link to download PDF."""
        if obj.result_pdf:
            return format_html(
                '<a href="{}" target="_blank" class="button">Pobierz PDF</a>',
                obj.result_pdf.url
            )
        return '-'
    result_pdf_link.short_description = 'Pobierz PDF'

    @admin.action(description='Oznacz jako skontaktowano')
    def mark_as_contacted(self, request, queryset):
        """Mark selected leads as contacted."""
        count = queryset.update(
            status='contacted',
            contacted_at=timezone.now(),
            contacted_by=request.user.get_full_name() or request.user.email
        )
        self.message_user(request, f'Oznaczono {count} leadów jako skontaktowane.')

    @admin.action(description='Przetwórz ponownie')
    def reprocess_leads(self, request, queryset):
        """Reprocess selected leads."""
        from .tasks import process_lead_task

        count = 0
        for lead in queryset:
            lead.status = 'pending'
            lead.processing_error = None
            lead.save()
            process_lead_task.delay(lead.id)
            count += 1

        self.message_user(request, f'Zlecono ponowne przetworzenie {count} leadów.')
