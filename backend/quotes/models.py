from django.db import models
from django.conf import settings
from materials.models import Material


def quote_image_path(instance, filename):
    return f'quotes/{instance.id or "temp"}/{filename}'


class Quote(models.Model):
    """Roof quote with dimensions, materials, and calculations."""
    ROOF_TYPES = [
        ('shed', 'Jednospadowy'),
        ('gable', 'Dwuspadowy'),
        ('gable_l', 'Dwuspadowy L'),
        ('hip', 'Czterospadowy'),
        ('hip_envelope', 'Kopertowy'),
        ('multi_hip', 'Wielospadowy'),
        ('multi_hip_l', 'Wielospadowy L'),
        ('mansard', 'Mansardowy'),
        ('half_hip', 'Naczółkowy'),
        ('skillion', 'Pulpitowy'),
        ('flat', 'Płaski'),
    ]
    
    STATUSES = [
        ('draft', 'Roboczy'),
        ('sent', 'Wysłano'),
        ('accepted', 'Zaakceptowano'),
        ('rejected', 'Odrzucono'),
    ]
    
    # Meta
    number = models.CharField(max_length=50, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quotes')
    status = models.CharField(max_length=20, choices=STATUSES, default='draft')
    
    # Client data
    client_name = models.CharField(max_length=200, blank=True)
    client_email = models.EmailField(blank=True)
    client_phone = models.CharField(max_length=20, blank=True)
    client_address = models.TextField(blank=True)
    
    # Roof data
    roof_type = models.CharField(max_length=20, choices=ROOF_TYPES, default='gable')
    plan_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    real_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pitch_angle = models.IntegerField(default=35)
    
    # Dimensions (JSON)
    dimensions = models.JSONField(default=dict, blank=True)
    # {"length": 12.5, "width": 8.0, "unit": "m"}
    
    # Comprehensive roof measurements (JSON)
    roof_measurements = models.JSONField(default=dict, blank=True)
    # {"ridge_length": 15, "valley_length": 8, "eave_length": 40, "gable_edge_left": 10, "gable_edge_right": 10}
    
    # Gasior elements (JSON)
    gasior_elements = models.JSONField(default=dict, blank=True)
    # {"junctions": 2, "corner_gasiors": 4, "start_gasiors": 2, "end_gasiors": 2}
    
    # Gutter system (JSON)
    gutter_system = models.JSONField(default=dict, blank=True)
    # {"corners": 4, "downpipes": 4, "end_caps": 4}
    
    # Obstacles
    obstacles = models.JSONField(default=list, blank=True)
    # [{"type": "chimney", "quantity": 2, "cost": 100}, ...]
    
    # Images
    original_image = models.ImageField(upload_to=quote_image_path, null=True, blank=True)
    processed_image = models.ImageField(upload_to=quote_image_path, null=True, blank=True)
    
    # AI data
    ai_extracted_data = models.JSONField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_processed = models.BooleanField(default=False)
    ai_processing = models.BooleanField(default=False)
    
    # Materials
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True)
    materials_breakdown = models.JSONField(default=dict, blank=True)
    
    # Financials
    margin_percent = models.IntegerField(default=35)
    vat_rate = models.IntegerField(default=23)
    total_net = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_gross = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # PDF
    pdf_file = models.FileField(upload_to='quotes/pdfs/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.number:
            from datetime import datetime
            now = datetime.now()
            count = Quote.objects.filter(
                created_at__year=now.year,
                created_at__month=now.month
            ).count() + 1
            self.number = f"{now.year}/{now.month:02d}/{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.number} - {self.client_name or 'Brak klienta'}"
