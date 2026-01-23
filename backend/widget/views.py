from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import logging

from .models import APIKey, EmailToken
from .authentication import WidgetAPIKeyAuthentication
from .permissions import HasValidOrigin
from .serializers import WidgetConfigSerializer
from .services import send_widget_submission_email
from .throttling import WidgetRateThrottle

from leads.models import Lead
from leads.tasks import process_lead_task  # Assuming this exists as per Plan

logger = logging.getLogger(__name__)

class WidgetConfigView(APIView):
    """Get widget configuration for frontend."""
    authentication_classes = [WidgetAPIKeyAuthentication]
    permission_classes = [HasValidOrigin]

    def get(self, request):
        company = request.user  # WidgetAPIKeyAuthentication returns company as user
        try:
            widget_config = company.widget_config
        except Exception:
            # Fallback if config doesn't exist (should not happen due to OneToOne)
            return Response({'error': 'Config not found'}, status=404)
            
        serializer = WidgetConfigSerializer(widget_config)
        return Response(serializer.data)


class WidgetSubmitView(APIView):
    """Handle widget form submission."""
    authentication_classes = [WidgetAPIKeyAuthentication]
    permission_classes = [HasValidOrigin]
    throttle_classes = [WidgetRateThrottle]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        email = request.data.get('email')
        phone = request.data.get('phone')
        uploaded_file = request.FILES.get('file')

        if not all([email, phone, uploaded_file]):
            return Response({'error': 'Wszystkie pola wymagane'}, status=400)

        # Validate file type/size if needed (handled partly by logic or serializer later)
        # For now, minimal validation.
        
        company = request.user
        widget_config = company.widget_config
        
        # Determine file type
        filename = uploaded_file.name.lower()
        file_type = 'jpg'
        if filename.endswith('.png'):
            file_type = 'png'
        elif filename.endswith('.pdf'):
            file_type = 'pdf'
        
        lead = Lead.objects.create(
            email=email,
            phone=phone,
            uploaded_file=uploaded_file,
            file_type=file_type,
            status='pending',
            source='widget',
            widget_config=widget_config,
            assigned_to=widget_config.auto_assign_to,
            widget_metadata={
                'referrer': request.headers.get('Referer'),
                'user_agent': request.headers.get('User-Agent'),
                'submitted_at': timezone.now().isoformat(),
            }
        )

        # Create Quote for Dashboard visibility
        quote_id = None
        try:
            from quotes.models import Quote
            
            # Determine target user (owner of the quote)
            target_user = widget_config.auto_assign_to
            if not target_user:
                target_user = company.users.first()
            
            if target_user:
                quote = Quote.objects.create(
                    user=target_user,
                    client_email=email,
                    client_phone=phone,
                    original_image=uploaded_file, # Same file
                    status='draft',
                    client_name=f"Lead {email}", # Placeholder
                )
                quote_id = quote.id
                logger.info(f"Created Quote {quote.number} for Lead {lead.public_uuid}")
            else:
                logger.warning(f"No user found for company {company.name}, skipping Quote creation")
                
        except Exception as q_err:
             logger.error(f"Failed to create Quote for submission: {q_err}")

        # Queue AI processing
        task = process_lead_task.delay(lead.id, quote_id=quote_id)
        lead.celery_task_id = task.id
        lead.save(update_fields=['celery_task_id'])

        # Create email token
        token = EmailToken.create_for_lead(lead, ip_address=request.META.get('REMOTE_ADDR'))
        
        # Send confirmation email
        send_widget_submission_email.delay(token.id)
        
        # Update stats
        widget_config.total_submissions += 1
        widget_config.save(update_fields=['total_submissions'])

        return Response({
            'success': True,
            'message': 'Link do wyników zostanie wysłany na email.',
            'estimated_time': '2-5 minut'
        }, status=201)


class EmailTokenStatusView(APIView):
    """Check lead status via email token (no auth required)."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        try:
            email_token = EmailToken.objects.select_related('lead').get(token=token)
        except EmailToken.DoesNotExist:
            return Response({'error': 'Nieprawidłowy token'}, status=404)

        if not email_token.is_valid():
            return Response({'error': 'Token wygasł'}, status=410)

        email_token.access_count += 1
        email_token.last_accessed_at = timezone.now()
        email_token.save(update_fields=['access_count', 'last_accessed_at'])

        lead = email_token.lead
        response = {
            'status': lead.status,
            'status_display': lead.get_status_display(),
        }

        if lead.status == 'completed':
            response.update({
                'roof_type': lead.roof_type,
                'pitch_angle': str(lead.pitch_angle) if lead.pitch_angle else None,
                'roof_area': str(lead.roof_area) if lead.roof_area else None,
                'estimated_price': str(lead.estimated_price_min),
                'pdf_url': f'/api/widget/download/{token}/' if lead.result_pdf else None,
            })
        
        return Response(response)

class EmailTokenDownloadView(APIView):
    """Download PDF via email token."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        try:
            email_token = EmailToken.objects.select_related('lead').get(token=token)
        except EmailToken.DoesNotExist:
             return Response({'error': 'Not found'}, status=404)
             
        if not email_token.is_valid():
             return Response({'error': 'Expired'}, status=410)
             
        lead = email_token.lead
        if not lead.result_pdf:
             return Response({'error': 'No PDF available'}, status=404)
        
        from django.http import FileResponse
        return FileResponse(lead.result_pdf.open('rb'), as_attachment=True, filename=f"wycena-{lead.public_uuid}.pdf")

# Dashboard Views (Placeholder or Basic)
from rest_framework.permissions import IsAuthenticated

class DashboardConfigView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.company:
            from users.models import Company
            # Create company dynamically if missing (legacy user patch)
            company_name = f"Firma {request.user.first_name or request.user.username}"
            company = Company.objects.create(name=company_name)
            request.user.company = company
            request.user.save(update_fields=['company'])

        company = request.user.company
        from .models import WidgetConfig
        
        # Ensure config exists (Robust get_or_create)
        if not hasattr(company, 'widget_config'):
             WidgetConfig.objects.create(company=company)
        
        serializer = WidgetConfigSerializer(company.widget_config)
        return Response(serializer.data)
        
    def post(self, request):
        if not request.user.company:
            # Should be handled by get() usually, but safe guard
             return Response({'error': 'User has no company'}, status=400)
             
        company = request.user.company
        config = company.widget_config
        serializer = WidgetConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class APIKeysListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.company:
             return Response([]) # No company = no keys
             
        company = request.user.company
        keys = APIKey.objects.filter(company=company).order_by('-created_at')
        from rest_framework import serializers
        class SimpleKeySerializer(serializers.ModelSerializer):
            class Meta:
                model = APIKey
                fields = ['id', 'name', 'public_key', 'created_at', 'last_used_at', 'total_requests', 'is_active']
        
        serializer = SimpleKeySerializer(keys, many=True)
        return Response(serializer.data)

class APIKeyCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if not request.user.company:
                from users.models import Company
                company_name = f"Firma {request.user.first_name or request.user.username}"
                company = Company.objects.create(name=company_name)
                request.user.company = company
                request.user.save(update_fields=['company'])
                
            company = request.user.company
            name = request.data.get('name', 'Widget API Key')

            public_key, secret_key = APIKey.generate_keys()

            api_key = APIKey.objects.create(
                company=company,
                name=name,
                public_key=public_key,
                secret_key_hash=APIKey.hash_secret(secret_key)
            )

            return Response({
                'id': api_key.id,
                'name': api_key.name,
                'public_key': public_key,
                'secret_key': secret_key,  # SHOWN ONLY ONCE!
                'created_at': api_key.created_at,
                'warning': 'Zapisz secret_key! Nie będzie pokazany ponownie.'
            }, status=201)
        except Exception as e:
            import traceback
            logger.error(f"Error creating API Key: {e}")
            logger.error(traceback.format_exc())
            return Response({'error': str(e)}, status=500)


class APIKeyDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, key_id):
        try:
            if not request.user.company:
                return Response({'error': 'No company'}, status=400)
            
            company = request.user.company
            api_key = APIKey.objects.filter(company=company, id=key_id).first()
            
            if not api_key:
                return Response({'error': 'Key not found'}, status=404)
            
            api_key.delete()
            return Response({'success': True}, status=200)
        except Exception as e:
            logger.error(f"Error deleting API Key: {e}")
            return Response({'error': str(e)}, status=500)

