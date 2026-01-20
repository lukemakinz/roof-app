import logging
from celery import shared_task
from django.core.files.base import ContentFile

from .models import Lead
from .services import process_roof_image, generate_result_pdf

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_lead_task(self, lead_id: int):
    """
    Process a lead's roof image using AI and generate PDF with results.

    This task:
    1. Marks the lead as processing
    2. Sends the image to AI for analysis
    3. Calculates price estimate
    4. Generates PDF with results
    5. Updates the lead with results
    """
    try:
        lead = Lead.objects.get(id=lead_id)
        logger.info(f"Processing lead {lead.public_uuid}")

        # Mark as processing
        lead.mark_processing()

        # Process the roof image with AI
        results = process_roof_image(lead.uploaded_file.path)

        if not results:
            lead.mark_failed("AI processing returned no results")
            return

        # Calculate price estimate based on roof area
        roof_area = results.get('powierzchnia_dachu_m2')
        if roof_area:
            # Base price per m2 (can be configured)
            price_per_m2 = 150  # PLN
            results['szacowana_cena_od'] = float(roof_area) * price_per_m2

        # Mark as completed with results
        lead.mark_completed(results)

        # Generate PDF
        try:
            pdf_content = generate_result_pdf(lead)
            if pdf_content:
                filename = f"wycena_{lead.public_uuid}.pdf"
                lead.result_pdf.save(filename, ContentFile(pdf_content), save=True)
                logger.info(f"PDF generated for lead {lead.public_uuid}")
        except Exception as pdf_error:
            logger.error(f"PDF generation failed for lead {lead.public_uuid}: {pdf_error}")
            # Don't fail the whole task if PDF generation fails

        logger.info(f"Lead {lead.public_uuid} processed successfully")

    except Lead.DoesNotExist:
        logger.error(f"Lead {lead_id} not found")
    except Exception as e:
        logger.error(f"Error processing lead {lead_id}: {e}")
        try:
            lead = Lead.objects.get(id=lead_id)
            lead.mark_failed(str(e))
        except Lead.DoesNotExist:
            pass

        # Retry on failure
        raise self.retry(exc=e)
