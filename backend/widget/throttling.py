from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from .models import APIKey

class WidgetRateThrottle(BaseThrottle):
    """
    Rate limit widget submissions based on Company settings.
    """
    
    def allow_request(self, request, view):
        # Only apply to authenticated requests via WidgetAPIKey
        if not request.auth or not isinstance(request.auth, APIKey):
            return True
            
        company = request.auth.company
        widget_config = company.widget_config
        
        # Key: widget_ratelimit:company_id
        cache_key = f"widget_ratelimit:{company.id}"
        history = cache.get(cache_key, [])
        
        # Clean old history (older than 1 hour)
        import time
        now = time.time()
        hour_ago = now - 3600
        
        # Filter history
        while history and history[0] < hour_ago:
            history.pop(0)
            
        if len(history) >= widget_config.rate_limit_per_hour:
             return False
             
        # Add timestamp
        history.append(now)
        cache.set(cache_key, history, 3600)
        
        return True
        
    def wait(self):
        return 60  # Retry after 60 seconds (generic)
