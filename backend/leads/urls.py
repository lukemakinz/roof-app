from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),

    # Lead submission
    path('submit/', views.submit_lead, name='submit'),

    # Results page
    path('wynik/<uuid:uuid>/', views.result_page, name='result'),

    # API endpoints
    path('api/status/<uuid:uuid>/', views.check_status, name='check_status'),
    path('api/pdf/<uuid:uuid>/', views.download_pdf, name='download_pdf'),
]
