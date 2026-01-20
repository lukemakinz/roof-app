from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # New minimalist lead capture system
    path('', include('leads.urls')),

    # ============================================
    # LEGACY API ENDPOINTS (commented out)
    # Uncomment to restore full CRM functionality
    # ============================================
    # path('api/auth/', include('users.urls')),
    # path('api/materials/', include('materials.urls')),
    # path('api/quotes/', include('quotes.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
