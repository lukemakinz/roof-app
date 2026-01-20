import os
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .models import Lead
from .tasks import process_lead_task


def landing_page(request):
    """Display the main landing page with upload form."""
    return render(request, 'leads/landing.html')


@csrf_exempt
@require_http_methods(["POST"])
def submit_lead(request):
    """Handle lead submission with file upload."""
    try:
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        uploaded_file = request.FILES.get('file')

        # Validate required fields
        if not email or not phone or not uploaded_file:
            return JsonResponse({
                'success': False,
                'error': 'Wszystkie pola są wymagane'
            }, status=400)

        # Validate file type
        file_name = uploaded_file.name.lower()
        if file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            file_type = 'jpg'
        elif file_name.endswith('.png'):
            file_type = 'png'
        elif file_name.endswith('.pdf'):
            file_type = 'pdf'
        else:
            return JsonResponse({
                'success': False,
                'error': 'Dozwolone formaty: JPG, PNG, PDF'
            }, status=400)

        # Validate file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'Maksymalny rozmiar pliku to 10MB'
            }, status=400)

        # Create lead
        lead = Lead.objects.create(
            email=email,
            phone=phone,
            uploaded_file=uploaded_file,
            file_type=file_type,
            status='pending'
        )

        # Queue processing task
        task = process_lead_task.delay(lead.id)
        lead.celery_task_id = task.id
        lead.save(update_fields=['celery_task_id'])

        return JsonResponse({
            'success': True,
            'uuid': str(lead.public_uuid),
            'message': 'Dziękujemy! Analizujemy Twój dach. Wyniki będą dostępne wkrótce.'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Wystąpił błąd: {str(e)}'
        }, status=500)


def result_page(request, uuid):
    """Display the results page for a specific lead."""
    lead = get_object_or_404(Lead, public_uuid=uuid)

    context = {
        'lead': lead,
        'is_processing': lead.status in ['pending', 'processing'],
        'is_completed': lead.status == 'completed',
        'is_failed': lead.status == 'failed',
    }

    return render(request, 'leads/result.html', context)


def check_status(request, uuid):
    """API endpoint to check lead processing status."""
    lead = get_object_or_404(Lead, public_uuid=uuid)

    response_data = {
        'status': lead.status,
        'status_display': lead.get_status_display(),
    }

    if lead.status == 'completed':
        response_data.update({
            'roof_type': lead.roof_type,
            'pitch_angle': str(lead.pitch_angle) if lead.pitch_angle else None,
            'roof_area': str(lead.roof_area) if lead.roof_area else None,
            'estimated_price': str(lead.estimated_price_min) if lead.estimated_price_min else None,
            'has_pdf': bool(lead.result_pdf),
        })
    elif lead.status == 'failed':
        response_data['error'] = lead.processing_error

    return JsonResponse(response_data)


def download_pdf(request, uuid):
    """Download the generated PDF for a lead."""
    lead = get_object_or_404(Lead, public_uuid=uuid)

    if not lead.result_pdf:
        raise Http404("PDF nie jest jeszcze dostępny")

    # Return the file
    response = FileResponse(
        lead.result_pdf.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="wycena_{uuid}.pdf"'
    return response
