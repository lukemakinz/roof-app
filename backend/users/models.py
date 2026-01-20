from django.contrib.auth.models import AbstractUser
from django.db import models


class Company(models.Model):
    """Company/firm that users belong to."""
    name = models.CharField(max_length=200)
    nip = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True)
    settings = models.JSONField(default=dict, blank=True)
    # settings: {"default_margin": 35, "default_vat": 23}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model with roles."""
    ROLE_CHOICES = [
        ('salesperson', 'Handlowiec'),
        ('manager', 'Manager'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='salesperson')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
