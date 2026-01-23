import logging
from celery import shared_task
from django.core.files.base import ContentFile

from .models import Lead
from .services import process_roof_image, generate_result_pdf
# from quotes.services.ai_processor import process_roof_image # Reverted to local service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_lead_task(self, lead_id: int, quote_id: int = None):
    """
    Process a lead's roof image using AI and generate PDF with results.
    Optional: Updates associated Quote.
    """
    try:
        lead = Lead.objects.get(id=lead_id)
        logger.info(f"Processing lead {lead.public_uuid}")

        # Mark as processing
        lead.mark_processing()

        # Process the roof image with AI (using local confirmed working service)
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

        # Update Quote if exists
        if quote_id:
            try:
                from quotes.models import Quote
                quote = Quote.objects.get(id=quote_id)
                
                # Update Quote fields from AI results
                quote.ai_extracted_data = results
                quote.ai_processed = True
                
                # Map basic fields
                quote.roof_type = results.get('typ_dachu', 'gable') # Fallback/Map
                
                # Extended mapping for roof type
                roof_type_map = {
                    'jednospadowy': 'shed',
                    'dwuspadowy': 'gable',
                    'dwuspadowy_l': 'gable_l',
                    'czterospadowy': 'hip', 
                    'kopertowy': 'hip_envelope',
                    'wielospadowy': 'multi_hip',
                    'wielospadowy_l': 'multi_hip_l',
                    'mansardowy': 'mansard',
                    'naczolkowy': 'half_hip',
                    'pulpitowy': 'skillion',
                    'plaski': 'flat'
                }
                typ_dachu = results.get('typ_dachu', 'dwuspadowy').lower()
                quote.roof_type = roof_type_map.get(typ_dachu, 'gable')

                if results.get('kat_nachylenia'):
                     quote.pitch_angle = int(float(results.get('kat_nachylenia')))
                
                # Map dimensions correctly (English keys)
                if results.get('wymiary_budynku'):
                     wymiary = results.get('wymiary_budynku')
                     quote.dimensions = {
                        'length': wymiary.get('dlugosc_m', 0),
                        'width': wymiary.get('szerokosc_m', 0),
                        'unit': 'm'
                     }
                     quote.plan_area = quote.dimensions['length'] * quote.dimensions['width']
                     
                if results.get('elementy_dodatkowe'):
                    elementy = results.get('elementy_dodatkowe')
                    quote.obstacles = []
                    if elementy.get('kominy_szt', 0) > 0:
                        quote.obstacles.append({'type': 'chimney', 'quantity': elementy['kominy_szt']})
                    if elementy.get('kominki_wentylacyjne_szt', 0) > 0:
                        quote.obstacles.append({'type': 'vent_pipe', 'quantity': elementy['kominki_wentylacyjne_szt']})
                    if elementy.get('okna_dachowe_szt', 0) > 0:
                        quote.obstacles.append({'type': 'skylight', 'quantity': elementy['okna_dachowe_szt']})
                    if elementy.get('wylazy_dachowe_szt', 0) > 0:
                        quote.obstacles.append({'type': 'roof_hatch', 'quantity': elementy['wylazy_dachowe_szt']})
                
                # Map confidence
                confidence_map = {'wysoka': 0.9, 'srednia': 0.7, 'niska': 0.4}
                pewnosc = results.get('pewnosc_oszacowania', 'srednia')
                quote.ai_confidence = confidence_map.get(pewnosc, 0.7)

                quote.save()
                logger.info(f"Quote {quote.number} updated with AI results")
            except Exception as q_error:
                logger.error(f"Error updating Quote {quote_id}: {q_error}")

        # Generate PDF
        try:
            pdf_content = generate_result_pdf(lead)
            if pdf_content:
                filename = f"wycena_{lead.public_uuid}.pdf"
                lead.result_pdf.save(filename, ContentFile(pdf_content), save=True)
                logger.info(f"PDF generated for lead {lead.public_uuid}")
                
                # Save PDF to Quote as well
                if quote_id:
                    try:
                        from quotes.models import Quote
                        quote = Quote.objects.get(id=quote_id)
                        quote.pdf_file.save(filename, ContentFile(pdf_content), save=True)
                    except Exception as q_pdf_error:
                        logger.error(f"Error saving PDF to Quote {quote_id}: {q_pdf_error}")

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
