from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
# from celery import shared_task # Celery optional for now, sticking to sync or simple threading if backend not ready?
# Plan said "from celery import shared_task". I will assume Celery is setup or I use it.
# But I saw in settings.py I added REDIS_URL.
# If Celery is not running, tasks will fail if async.
# I will use a simple async wrapper or just sync for MVP if safe.
# Given settings.py has CELERY_BROKER_URL, let's try to use shared_task but with fallback?
# Or just standart implementation.

try:
    from celery import shared_task
except ImportError:
    # Dummy decorator if celery not installed
    def shared_task(func):
        return func

from .models import EmailToken

@shared_task
def send_widget_submission_email(token_id):
    """Send email with access link to lead."""
    try:
        token = EmailToken.objects.select_related('lead', 'lead__widget_config__company').get(id=token_id)
        lead = token.lead
        company = token.lead.widget_config.company

        access_url = f"{settings.FRONTEND_URL}/widget/results/{token.token}/"

        context = {
            'company_name': company.name,
            'company_logo': company.logo.url if company.logo else None,
            'access_url': access_url,
            'expiration_days': 7,
        }

        html_message = render_to_string('widget/emails/submission.html', context)

        send_mail(
            subject=f'Wycena dachu - {company.name}',
            message=f'Link do wyników: {access_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[lead.email],
            html_message=html_message,
        )
    except Exception as e:
        print(f"Error sending email: {e}")

@shared_task
def send_results_ready_email(lead_id):
    """Send email when analysis is completed."""
    try:
        from leads.models import Lead
        lead = Lead.objects.select_related('widget_config__company').get(id=lead_id, source='widget')

        token = lead.email_tokens.filter(is_used=False).order_by('-created_at').first()
        if not token:
            token = EmailToken.create_for_lead(lead)

        company = lead.widget_config.company
        access_url = f"{settings.FRONTEND_URL}/widget/results/{token.token}/"
        
        context = {
            'company_name': company.name,
            'company_logo': company.logo.url if company.logo else None,
            'access_url': access_url,
            'expiration_days': 7,
            'is_ready': True
        }

        html_message = render_to_string('widget/emails/submission.html', context)

        send_mail(
            subject=f'Twoja wycena jest gotowa - {company.name}',
            message=f'Twoja wycena dachu jest gotowa. Zobacz wyniki: {access_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[lead.email],
            html_message=html_message,
        )
    except Exception as e:
        print(f"Error sending results email: {e}")
