from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.utils.crypto import get_random_string
import uuid
import secrets
import hashlib

class WidgetConfig(models.Model):
    POSITION_CHOICES = [
        ('bottom-right', 'Dolny prawy'),
        ('bottom-left', 'Dolny lewy'),
        ('top-right', 'Górny prawy'),
        ('top-left', 'Górny lewy'),
    ]

    company = models.OneToOneField('users.Company', on_delete=models.CASCADE, related_name='widget_config')
    is_active = models.BooleanField(default=True, db_index=True)

    # Customizacja wizualna
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    secondary_color = models.CharField(max_length=7, default='#1E293B')
    font_family = models.CharField(max_length=100, default='Inter, sans-serif')
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='bottom-right')

    # Teksty
    button_text = models.CharField(max_length=100, default='Wycena dachu')
    header_text = models.CharField(max_length=200, default='Bezpłatna wycena dachu')
    description_text = models.TextField(default='Prześlij zdjęcie dachu, a my przygotujemy wycenę.')

    # Bezpieczeństwo
    allowed_domains = models.JSONField(default=list)  # ["example.com", "*.example.com"]
    rate_limit_per_hour = models.IntegerField(default=100)

    # Ustawienia
    notification_email = models.EmailField(blank=True, null=True)
    auto_assign_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)

    # Statystyki
    total_submissions = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Widget Config for {self.company}"

class APIKey(models.Model):
    company = models.ForeignKey('users.Company', on_delete=models.CASCADE, related_name='api_keys')

    # Klucze
    public_key = models.CharField(max_length=64, unique=True, db_index=True, editable=False)
    # Format: pk_abc123xyz...

    secret_key_hash = models.CharField(max_length=128, editable=False)
    # SHA256 hash (NIGDY plaintext w DB!)

    # Metadane
    name = models.CharField(max_length=200)  # "Widget strona główna"
    is_active = models.BooleanField(default=True, db_index=True)

    # Tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    total_requests = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_keys():
        """Returns (public_key, secret_key_plaintext)"""
        public_key = f"pk_{get_random_string(32)}"
        secret_key = f"sk_{secrets.token_urlsafe(48)}"
        return public_key, secret_key

    @staticmethod
    def hash_secret(secret_key):
        return hashlib.sha256(secret_key.encode()).hexdigest()

    def verify_secret(self, secret_key):
        return secrets.compare_digest(self.secret_key_hash, self.hash_secret(secret_key))

    def increment_usage(self):
        self.total_requests += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['total_requests', 'last_used_at'])

    def __str__(self):
        return f"{self.name} ({self.public_key[:10]}...)"

class EmailToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    lead = models.ForeignKey('leads.Lead', on_delete=models.CASCADE, related_name='email_tokens')
    email = models.EmailField()

    # Status
    is_used = models.BooleanField(default=False, db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)  # default: 7 dni

    # Tracking
    access_count = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    created_ip = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_for_lead(cls, lead, ip_address=None):
        return cls.objects.create(
            lead=lead,
            email=lead.email,
            expires_at=timezone.now() + timedelta(days=7),
            created_ip=ip_address
        )

    def is_valid(self):
        # Allow multiple uses as long as not expired (e.g. user refreshes page)
        # Or do we want strict single-use for viewing? 
        # PRD says "single-use token" but usage flow often requires refreshing.
        # Plan says "is_valid() return not self.is_used"
        # I will stick to expiration date for validity check, and track usage.
        # But wait, plan code says: `return not self.is_used and ...`
        # Let's check PRD. "Możliwość: single-use token".
        # If I strictly enforce single use, refreshing the page will break it.
        # For now I'll stick to the plan but maybe relax "is_used" or treat "mark_used" only when actions are taken?
        # Actually, for just VIEWING status, we probably want it reusable until expiry.
        # But for security, maybe we issue a session token after first link click?
        # Let's follow the Plan's code exactly primarily:
        return not self.is_used and timezone.now() <= self.expires_at

    def mark_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])
    
    def __str__(self):
        return f"Token {self.token} for {self.email}"
