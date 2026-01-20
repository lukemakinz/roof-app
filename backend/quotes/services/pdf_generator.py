"""
PDF generation service using WeasyPrint.
"""
import os
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def generate_quote_pdf(quote):
    """
    Generate PDF for a quote and save it to the quote model.
    
    Returns the saved file path.
    """
    if not WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint is not installed")
    
    # Prepare context
    context = {
        'quote': quote,
        'quote_number': quote.number,
        'date': quote.created_at.strftime('%d.%m.%Y'),
        'client_name': quote.client_name or 'Klient',
        'client_email': quote.client_email,
        'client_phone': quote.client_phone,
        'client_address': quote.client_address,
        'roof_type': quote.get_roof_type_display(),
        'pitch_angle': quote.pitch_angle,
        'plan_area': quote.plan_area,
        'real_area': quote.real_area,
        'materials': quote.materials_breakdown,
        'total_net': quote.total_net,
        'total_gross': quote.total_gross,
        'vat_rate': quote.vat_rate,
        'margin_percent': quote.margin_percent,
        'user': quote.user,
    }
    
    # Calculate VAT amount
    if quote.total_net and quote.total_gross:
        context['vat_amount'] = float(quote.total_gross) - float(quote.total_net)
    
    # Calculate labor cost
    if quote.materials_breakdown:
        materials_sum = sum(
            m.get('total', 0) 
            for m in quote.materials_breakdown.values() 
            if isinstance(m, dict)
        )
        context['materials_net'] = materials_sum
        context['labor_net'] = float(quote.total_net or 0) - materials_sum if quote.total_net else 0
    
    # Render HTML
    html_string = render_to_string('quotes/pdf_template.html', context)
    
    # Generate PDF
    pdf_file = HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()
    
    # Save to quote
    filename = f'oferta_{quote.number.replace("/", "-")}.pdf'
    quote.pdf_file.save(filename, ContentFile(pdf_file), save=True)
    
    return quote.pdf_file.path
