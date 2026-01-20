from django.db import models


class Material(models.Model):
    """Roofing materials with pricing and configuration."""
    CATEGORY_CHOICES = [
        ('metal_tile', 'Blachodachówka'),
        ('ceramic', 'Dachówka ceramiczna'),
        ('bitumen', 'Papa'),
        ('metal_sheet', 'Blacha trapezowa'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    price_per_m2 = models.DecimalField(max_digits=8, decimal_places=2)
    waste_factor = models.DecimalField(max_digits=4, decimal_places=2, default=1.12)
    config = models.JSONField(default=dict, blank=True)
    # config: {
    #   "battens_spacing_cm": 32,
    #   "counter_battens": true,
    #   "screws_per_m2": 7,
    #   "ridge_tape": true,
    #   "membrane_price_m2": 7,
    #   "battens_price_mb": 4,
    #   "counter_battens_price_mb": 5,
    #   "screws_price_per_100": 30,
    #   "ridge_tape_price_mb": 15
    # }
    active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.price_per_m2} PLN/m²)"
