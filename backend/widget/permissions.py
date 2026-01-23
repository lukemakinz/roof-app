from rest_framework import permissions
from .validators import validate_origin
from .models import APIKey

class HasValidOrigin(permissions.BasePermission):
    """Check if Origin header is in allowed_domains."""

    message = 'Origin domain not allowed'

    def has_permission(self, request, view):
        if not request.auth or not isinstance(request.auth, APIKey):
            # If not authenticated via WidgetAPIKey, skip this check (e.g. Dashboard access)
            return True

        origin = request.headers.get('Origin') or request.headers.get('Referer')
        print(f"DEBUG: HasValidOrigin - Origin: {origin}")
        
        if not origin:
            # Server-to-server requests are allowed if they have the keys
            # But normally browsers send Origin. 
            # If strictly for widget, we might want to enforce Origin.
            # strict/permissive? Let's be permissive for now but maybe log warning.
            return True 
            
        # Explicit bypass for localhost (failsafe)
        if 'localhost' in origin or '127.0.0.1' in origin:
            print("DEBUG: HasValidOrigin - Localhost bypass")
            return True

        widget_config = request.auth.company.widget_config
        allowed = validate_origin(origin, widget_config.allowed_domains)
        print(f"DEBUG: HasValidOrigin - Allowed Domains: {widget_config.allowed_domains}")
        print(f"DEBUG: HasValidOrigin - Result: {allowed}")
        return allowed
