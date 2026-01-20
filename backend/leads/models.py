import uuid
from django.db import models
from django.utils import timezone


class Lead(models.Model):
    """Lead model for roof analysis requests from potential customers."""

    STATUS_CHOICES = [
        ('pending', 'Oczekujący'),
        ('processing', 'Przetwarzanie'),
        ('completed', 'Zakończony'),
        ('failed', 'Błąd'),
        ('contacted', 'Skontaktowano'),
        ('converted', 'Skonwertowany'),
    ]

    SOURCE_CHOICES = [
        ('landing', 'Landing Page'),
        ('widget', 'Widget'),
    ]

    FILE_TYPE_CHOICES = [
        ('jpg', 'JPEG'),
        ('png', 'PNG'),
        ('pdf', 'PDF'),
    ]

    # Public access UUID
    public_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        verbose_name='Publiczny UUID'
    )

    # Contact information
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Numer telefonu')

    # Source info
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default='landing',
        db_index=True,
        verbose_name='Źródło'
    )
    widget_config = models.ForeignKey(
        'widget.WidgetConfig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        verbose_name='Konfiguracja Widgetu'
    )
    widget_metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Metadane widgetu'
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads',
        verbose_name='Przypisany handlowiec'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Status'
    )

    # Uploaded file
    uploaded_file = models.FileField(
        upload_to='leads/uploads/%Y/%m/',
        verbose_name='Plik'
    )
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        verbose_name='Typ pliku'
    )

    # AI Analysis Results
    roof_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Typ dachu'
    )
    pitch_angle = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Kąt nachylenia (°)'
    )
    roof_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Powierzchnia dachu (m²)'
    )
    dimensions = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Wymiary'
    )
    roof_elements = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Elementy dachu'
    )

    # Raw AI response for debugging
    ai_raw_response = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Surowa odpowiedź AI'
    )
    ai_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Pewność AI (%)'
    )
    ai_warnings = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Ostrzeżenia AI'
    )

    # Price estimate
    estimated_price_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Szacowana cena od (PLN)'
    )

    # Generated PDF
    result_pdf = models.FileField(
        upload_to='leads/pdfs/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='PDF z wynikami'
    )

    # Processing info
    processing_error = models.TextField(
        blank=True,
        null=True,
        verbose_name='Błąd przetwarzania'
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ID zadania Celery'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data utworzenia'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Data aktualizacji'
    )
    processing_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Rozpoczęcie przetwarzania'
    )
    processing_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Zakończenie przetwarzania'
    )

    # Sales tracking
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notatki handlowca'
    )
    contacted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data kontaktu'
    )
    contacted_by = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Kontaktował'
    )

    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leady'
        ordering = ['-created_at']

    def __str__(self):
        return f"Lead {self.public_uuid} - {self.email} ({self.get_status_display()})"

    def mark_processing(self):
        """Mark lead as processing."""
        self.status = 'processing'
        self.processing_started_at = timezone.now()
        self.save(update_fields=['status', 'processing_started_at', 'updated_at'])

    def mark_completed(self, results: dict):
        """Mark lead as completed with AI results."""
        self.status = 'completed'
        self.processing_completed_at = timezone.now()

        # Extract results - using structure from ai_processor.py
        self.roof_type = results.get('typ_dachu')
        self.pitch_angle = results.get('kat_nachylenia')

        # Surface area is nested in 'pomiary'
        pomiary = results.get('pomiary', {})
        self.roof_area = pomiary.get('powierzchnia_dachu_m2')

        # Dimensions are in 'wymiary_budynku', not 'wymiary'
        self.dimensions = results.get('wymiary_budynku')

        # Elements are in 'elementy_dodatkowe' with '_szt' suffixes
        elementy = results.get('elementy_dodatkowe', {})
        gasiory = results.get('elementy_gasiorowe', {})
        odwodnienie = results.get('system_odwodnienia', {})

        self.roof_elements = {
            # Elementy dodatkowe
            'kominy': elementy.get('kominy_szt', 0),
            'kominki_wentylacyjne': elementy.get('kominki_wentylacyjne_szt', 0),
            'okna_dachowe': elementy.get('okna_dachowe_szt', 0),
            'wylazy_dachowe': elementy.get('wylazy_dachowe_szt', 0),
            # Elementy gąsiorowe
            'trojniki': gasiory.get('trojniki_szt', 0),
            'gasiory_narozne': gasiory.get('gasiory_narozne_szt', 0),
            'gasiory_poczatkowe': gasiory.get('gasiory_poczatkowe_szt', 0),
            'gasiory_koncowe': gasiory.get('gasiory_koncowe_szt', 0),
            # System odwodnienia
            'narozniki_rynien': odwodnienie.get('narozniki_rynien_szt', 0),
            'rury_spustowe': odwodnienie.get('rury_spustowe_szt', 0),
            'zaslepki_rynien': odwodnienie.get('zaslepki_rynien_szt', 0),
        }

        self.ai_raw_response = results

        # Confidence mapping from string to percentage
        pewnosc = results.get('pewnosc_oszacowania', 'srednia')
        confidence_map = {'niska': 30, 'srednia': 60, 'wysoka': 90}
        self.ai_confidence = confidence_map.get(pewnosc, 60)

        self.ai_warnings = results.get('validation_warnings', [])
        self.estimated_price_min = results.get('szacowana_cena_od')

        self.save()

    def mark_failed(self, error: str):
        """Mark lead as failed with error message."""
        self.status = 'failed'
        self.processing_error = error
        self.processing_completed_at = timezone.now()
        self.save(update_fields=['status', 'processing_error', 'processing_completed_at', 'updated_at'])

    def mark_contacted(self, by: str = None):
        """Mark lead as contacted."""
        self.status = 'contacted'
        self.contacted_at = timezone.now()
        if by:
            self.contacted_by = by
        self.save(update_fields=['status', 'contacted_at', 'contacted_by', 'updated_at'])
