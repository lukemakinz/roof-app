from django.urls import path
from . import views

app_name = 'widget'

urlpatterns = [
    # Public widget API (WidgetAPIKey auth)
    path('config/', views.WidgetConfigView.as_view(), name='config'),
    path('submit/', views.WidgetSubmitView.as_view(), name='submit'),
    path('status/<uuid:token>/', views.EmailTokenStatusView.as_view(), name='status'),
    path('download/<uuid:token>/', views.EmailTokenDownloadView.as_view(), name='download'),

    # Dashboard API (JWT auth - IsAuthenticated check inside views)
    path('dashboard/config/', views.DashboardConfigView.as_view(), name='dashboard-config'),
    path('dashboard/api-keys/', views.APIKeysListView.as_view(), name='dashboard-keys-list'),
    path('dashboard/api-keys/create/', views.APIKeyCreateView.as_view(), name='dashboard-keys-create'),
    path('dashboard/api-keys/<int:key_id>/delete/', views.APIKeyDeleteView.as_view(), name='dashboard-keys-delete'),
]
