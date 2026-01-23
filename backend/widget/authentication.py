from rest_framework import authentication, exceptions
from urllib.parse import unquote
from .models import APIKey

class WidgetAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    Simple API key authentication for widget.

    Client headers:
        X-Widget-Public-Key: pk_xxxxx
        X-Widget-Secret-Key: sk_xxxxx
    """

    def authenticate(self, request):
        public_key = request.headers.get('X-Widget-Public-Key')
        secret_key = request.headers.get('X-Widget-Secret-Key')
        
        print(f"DEBUG: Auth - Headers keys: PK={public_key}, SK={'*' * 5 if secret_key else 'None'}")
        
        # Decode URL-encoded keys (for special characters in headers)
        if public_key:
            public_key = unquote(public_key)
        if secret_key:
            secret_key = unquote(secret_key)

        if not public_key or not secret_key:
            print("DEBUG: Auth - Missing keys")
            return None

        try:
            api_key = APIKey.objects.select_related('company', 'company__widget_config').get(
                public_key=public_key,
                is_active=True
            )
        except APIKey.DoesNotExist:
            print("DEBUG: Auth - APIKey DoesNotExist or Inactive")
            raise exceptions.AuthenticationFailed('Invalid API key')
            
        if not api_key.verify_secret(secret_key):
            print("DEBUG: Auth - Invalid secret")
            raise exceptions.AuthenticationFailed('Invalid secret key')

        if not api_key.verify_secret(secret_key):
            raise exceptions.AuthenticationFailed('Invalid secret key')

        if not hasattr(api_key.company, 'widget_config') or not api_key.company.widget_config.is_active:
            raise exceptions.AuthenticationFailed('Widget is disabled')

        api_key.increment_usage()

        # Return (company, api_key)
        # We return api_key as 'auth' so we can access it in permissions
        return (api_key.company, api_key)
