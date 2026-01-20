from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

from .models import Quote
from .serializers import (
    QuoteListSerializer, QuoteDetailSerializer, QuoteCreateSerializer,
    QuoteUploadSerializer, QuoteDimensionsSerializer, QuoteCalculateSerializer
)
from .services.calculator import calculate_roof_materials
from .services.ai_processor import process_roof_image
from materials.models import Material


class QuoteViewSet(viewsets.ModelViewSet):
    """ViewSet for Quote CRUD and special actions."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'manager':
            return Quote.objects.all()
        return Quote.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        if self.action == 'create':
            return QuoteCreateSerializer
        return QuoteDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request, pk=None):
        """Upload roof image for a quote."""
        quote = self.get_object()
        serializer = QuoteUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        quote.original_image = serializer.validated_data['image']
        quote.ai_processed = False
        quote.save()
        
        return Response({
            'message': 'Zdjęcie przesłane pomyślnie',
            'image_url': request.build_absolute_uri(quote.original_image.url)
        })
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process uploaded image with AI."""
        quote = self.get_object()
        
        if not quote.original_image:
            return Response(
                {'error': 'Najpierw prześlij zdjęcie dachu'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quote.ai_processing = True
        quote.save()
        
        try:
            # Process image
            result = process_roof_image(quote.original_image.path)
            
            if result['success']:
                data = result['data']
                
                # Update quote with AI data
                quote.ai_extracted_data = data
                
                # Map Polish response to model fields
                # Roof type mapping (extended)
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
                typ_dachu = data.get('typ_dachu', 'dwuspadowy').lower()
                quote.roof_type = roof_type_map.get(typ_dachu, 'gable')
                
                # Pitch angle
                if data.get('kat_nachylenia'):
                    quote.pitch_angle = int(data['kat_nachylenia'])
                
                # Building dimensions
                wymiary = data.get('wymiary_budynku', {})
                quote.dimensions = {
                    'length': wymiary.get('dlugosc_m', 10),
                    'width': wymiary.get('szerokosc_m', 8),
                    'unit': 'm'
                }
                
                # Calculate plan area
                dims = quote.dimensions
                if dims.get('length') and dims.get('width'):
                    quote.plan_area = dims['length'] * dims['width']
                
                # Roof measurements (ridges, valleys, eaves)
                pomiary = data.get('pomiary', {})
                quote.roof_measurements = {
                    'surface_area': pomiary.get('powierzchnia_dachu_m2', 0),
                    'gable_edge_left': pomiary.get('dlugosc_krawedzi_szczytowych_lewych_m', 0),
                    'gable_edge_right': pomiary.get('dlugosc_krawedzi_szczytowych_prawych_m', 0),
                    'ridge_length': pomiary.get('dlugosc_kalenic_m', 0),
                    'valley_length': pomiary.get('dlugosc_koszy_m', 0),
                    'eave_length': pomiary.get('dlugosc_okapow_m', 0)
                }
                
                # Gasior elements
                gasiory = data.get('elementy_gasiorowe', {})
                quote.gasior_elements = {
                    'junctions': gasiory.get('trojniki_szt', 0),
                    'corner_gasiors': gasiory.get('gasiory_narozne_szt', 0),
                    'start_gasiors': gasiory.get('gasiory_poczatkowe_szt', 0),
                    'end_gasiors': gasiory.get('gasiory_koncowe_szt', 0)
                }
                
                # Gutter system
                rynny = data.get('system_odwodnienia', {})
                quote.gutter_system = {
                    'corners': rynny.get('narozniki_rynien_szt', 0),
                    'downpipes': rynny.get('rury_spustowe_szt', 0),
                    'end_caps': rynny.get('zaslepki_rynien_szt', 0)
                }
                
                # Obstacles from additional elements
                elementy = data.get('elementy_dodatkowe', {})
                quote.obstacles = []
                if elementy.get('kominy_szt', 0) > 0:
                    quote.obstacles.append({'type': 'chimney', 'quantity': elementy['kominy_szt']})
                if elementy.get('kominki_wentylacyjne_szt', 0) > 0:
                    quote.obstacles.append({'type': 'vent_pipe', 'quantity': elementy['kominki_wentylacyjne_szt']})
                if elementy.get('okna_dachowe_szt', 0) > 0:
                    quote.obstacles.append({'type': 'skylight', 'quantity': elementy['okna_dachowe_szt']})
                if elementy.get('wylazy_dachowe_szt', 0) > 0:
                    quote.obstacles.append({'type': 'roof_hatch', 'quantity': elementy['wylazy_dachowe_szt']})
                
                # Confidence mapping
                confidence_map = {'wysoka': 0.9, 'srednia': 0.7, 'niska': 0.4}
                quote.ai_confidence = confidence_map.get(data.get('pewnosc_oszacowania', 'srednia'), 0.7)
                
                quote.ai_processed = True
                quote.ai_processing = False
                quote.save()
                
                return Response({
                    'message': 'Analiza zakończona pomyślnie',
                    'data': data
                })
            else:
                quote.ai_processing = False
                quote.save()
                return Response(
                    {'error': result.get('error', 'Błąd przetwarzania')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            quote.ai_processing = False
            quote.save()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get AI processing status."""
        quote = self.get_object()
        return Response({
            'ai_processing': quote.ai_processing,
            'ai_processed': quote.ai_processed,
            'ai_confidence': quote.ai_confidence
        })
    
    @action(detail=True, methods=['patch'])
    def dimensions(self, request, pk=None):
        """Update dimensions manually."""
        quote = self.get_object()
        serializer = QuoteDimensionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Update dimensions
        quote.dimensions = {
            'length': data['length'],
            'width': data['width'],
            'unit': 'm'
        }
        
        if 'pitch_angle' in data:
            quote.pitch_angle = data['pitch_angle']
        
        if 'roof_type' in data:
            quote.roof_type = data['roof_type']
        
        # Recalculate plan area
        quote.plan_area = data['length'] * data['width']
        quote.save()
        
        return Response(QuoteDetailSerializer(quote, context={'request': request}).data)
    
    @action(detail=True, methods=['patch'])
    def obstacles(self, request, pk=None):
        """Update obstacles."""
        quote = self.get_object()
        obstacles = request.data.get('obstacles', [])
        quote.obstacles = obstacles
        quote.save()
        
        return Response({'obstacles': quote.obstacles})
    
    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calculate materials for the quote."""
        quote = self.get_object()
        serializer = QuoteCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        material = get_object_or_404(Material, pk=data['material_id'], active=True)
        
        # Update margin if provided
        if 'margin_percent' in data:
            quote.margin_percent = data['margin_percent']
        
        quote.material = material
        quote.save()
        
        # Perform calculation
        result = calculate_roof_materials(quote, material)
        
        # Update quote with results
        quote.plan_area = result['plan_area']
        quote.real_area = result['real_area']
        quote.materials_breakdown = result['materials']
        quote.total_net = result['summary']['total_net']
        quote.total_gross = result['summary']['total_gross']
        quote.save()
        
        return Response({
            **result,
            'quote': QuoteDetailSerializer(quote, context={'request': request}).data
        })
    
    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """Generate PDF for the quote."""
        quote = self.get_object()
        
        # Update client data if provided
        client_data = ['client_name', 'client_email', 'client_phone', 'client_address']
        for field in client_data:
            if field in request.data:
                setattr(quote, field, request.data[field])
        quote.save()
        
        # Generate PDF
        try:
            from .services.pdf_generator import generate_quote_pdf
            pdf_path = generate_quote_pdf(quote)
            quote.refresh_from_db()
            
            return Response({
                'message': 'PDF wygenerowany pomyślnie',
                'pdf_url': request.build_absolute_uri(quote.pdf_file.url) if quote.pdf_file else None
            })
        except Exception as e:
            return Response(
                {'error': f'Błąd generowania PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a quote."""
        original = self.get_object()
        
        # Create copy
        new_quote = Quote.objects.create(
            user=request.user,
            status='draft',
            client_name=original.client_name,
            client_email=original.client_email,
            client_phone=original.client_phone,
            client_address=original.client_address,
            roof_type=original.roof_type,
            plan_area=original.plan_area,
            real_area=original.real_area,
            pitch_angle=original.pitch_angle,
            dimensions=original.dimensions,
            obstacles=original.obstacles,
            material=original.material,
            margin_percent=original.margin_percent,
            vat_rate=original.vat_rate
        )
        
        return Response(
            QuoteDetailSerializer(new_quote, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
