WYMAGANIA MVP - Aplikacja do wycen dachów
1. CEL PRODUKTU
Problem: Handlowiec potrzebuje 10 minut na wycenę dachu (ręczne mierzenie, Excel, formatowanie PDF)
Rozwiązanie: Aplikacja mobilna/webowa, która w 2-3 minuty:

Ekstrahuje wymiary z rzutu dachu (AI)
Pozwala zweryfikować/poprawić dane
Kalkuluje materiały automatycznie
Generuje profesjonalną ofertę PDF

Target: 70-80% redukcja czasu wyceny

2. TECH STACK
Backend

Python 3.12
Django 5.0
Django REST Framework
PostgreSQL 15+
Redis 7+
Celery 5+

Frontend

React 18
JavaScript (bez TypeScript)
TailwindCSS 3+
Konva.js (canvas manipulation)
React Query (server state)
Zustand (client state)

AI/ML

Claude 3.5 Sonnet API (primary vision model)
OpenCV (image preprocessing)
Pillow (image manipulation)

Infrastructure

Docker + docker-compose
S3/DigitalOcean Spaces (file storage)
GitHub Actions (CI/CD)


3. USER FLOW (MVP)
1. LOGIN
   ↓
2. UPLOAD ZDJĘCIA/PDF RZUTU DACHU
   ↓
3. AI PROCESSING (3-5 sek)
   - Wykrycie typu dachu
   - Ekstrakcja wymiarów
   - Wykrycie przeszkód
   ↓
4. WERYFIKACJA INTERAKTYWNA
   - Podgląd zdjęcia z nałożonymi wymiarami
   - Edycja wymiarów (inline)
   - Podanie kąta nachylenia (slider/input)
   - Zarządzanie przeszkodami (kominy, okna)
   ↓
5. WYBÓR MATERIAŁU
   - 5 predefiniowanych presetów
   - Live preview obliczeń
   ↓
6. KALKULACJA AUTOMATYCZNA
   - Powierzchnia rzeczywista (z kątem)
   - Materiały + ilości
   - Ceny
   ↓
7. GENEROWANIE OFERTY PDF
   - Dane klienta (input)
   - Zestawienie materiałów
   - Podsumowanie finansowe
   ↓
8. WYSŁANIE/POBRANIE PDF
Czas całkowity: 90-180 sekund

4. FUNKCJONALNOŚCI (MUST HAVE)
4.1 Autentykacja

 Rejestracja (email + hasło)
 Login (email + hasło)
 Resetowanie hasła (email link)
 JWT auth (access + refresh tokens)
 Role: Handlowiec, Manager

4.2 Upload i AI Processing
Upload:

 Drag & drop lub file picker
 Wspierane formaty: JPEG, PNG, PDF
 Max rozmiar: 10 MB
 Upload do S3/Spaces
 Preview przed procesowaniem

AI Processing (Celery async task):

 Image preprocessing:

Auto-rotate (deskew)
Contrast enhancement
Noise reduction


 Claude API call:

Wykrycie typu dachu (gable, hip, mansard, flat)
Ekstrakcja wymiarów zewnętrznych (długość × szerokość)
Wykrycie przeszkód (kominy, okna)
Confidence score


 Zapis wyników do DB (JSON field)

API Response:
json{
  "roof_type": "gable",
  "dimensions": {
    "length": 12.5,
    "width": 8.0,
    "unit": "m"
  },
  "obstacles": [
    {"type": "chimney", "quantity": 2},
    {"type": "skylight", "quantity": 3}
  ],
  "confidence": 0.87,
  "pitch_angle": null
}
```

### 4.3 Interaktywna weryfikacja

**Podgląd z wymiarami (Konva.js):**
- [x] Wyświetl uploaded image jako background
- [x] Overlay: linie + tekst z wymiarami
- [x] Zoom/pan (pinch, scroll)
- [x] Kliknięcie w wymiar → inline edit
- [x] Auto-save po edycji

**Edycja wymiarów:**
- [x] Inline input (kliknij "12.5m" → edytowalny)
- [x] Walidacja (min 2m, max 50m)
- [x] Live update obliczeń po zmianie

**Kąt nachylenia:**
- [x] Slider 15° - 60° (default: 35°)
- [x] Presety: "Płaski (25°)", "Standard (35°)", "Stromy (45°)"
- [x] Input manual (możliwość wpisania dokładnej wartości)
- [x] Live preview powierzchni przy zmianie kąta

**Przeszkody:**
```
Wykryte elementy:
☑ 2 kominy
☑ 3 okna dachowe

[+ Dodaj komin] [+ Dodaj okno]

Każdy komin: -1m² + 50 PLN obróbki
Każde okno: -0.5m² + 80 PLN
4.4 Baza materiałów
Model:
pythonclass Material(models.Model):
    name = CharField(max_length=200)  # "Pruszyński Standard"
    category = CharField(choices=CATEGORIES)  # metal_tile, ceramic, etc.
    price_per_m2 = DecimalField(max_digits=8, decimal_places=2)
    waste_factor = DecimalField(default=1.12)  # 12% odpadu
    config = JSONField(default=dict)
    # config: {
    #   "battens_spacing_cm": 32,
    #   "counter_battens": true,
    #   "screws_per_m2": 7,
    #   "ridge_tape": true
    # }
    active = BooleanField(default=True)
Predefiniowane presety (fixtures/seed data):

Blachodachówka ekonomiczna (40 PLN/m²)
Blachodachówka standard (50 PLN/m²)
Blachodachówka premium (65 PLN/m²)
Dachówka ceramiczna (85 PLN/m²)
Papa termozgrzewalna (35 PLN/m²)

4.5 Kalkulacja automatyczna
Algorytm:
python# 1. Powierzchnia rzeczywista
plan_area = length × width
real_area = plan_area / cos(pitch_angle_radians)

# 2. Z odpadem
material_needed = real_area × waste_factor

# 3. Konstrukcja
rafter_length = sqrt((width/2)² + height²)
battens_meters = rafter_length × (length / battens_spacing)
counter_battens_meters = length × number_of_rafters

# 4. Drobne
screws_quantity = material_needed × screws_per_m2
ridge_length = length

# 5. Przeszkody
obstacles_area_reduction = sum(obstacle.area)
obstacles_extra_cost = sum(obstacle.extra_cost)

# 6. Koszty
materials_net = sum(all_material_costs)
labor_cost = materials_net × labor_margin_percent
total_net = materials_net + labor_cost
vat = total_net × vat_rate
total_gross = total_net + vat
Output JSON:
json{
  "plan_area": 100.0,
  "real_area": 122.0,
  "materials": {
    "roofing": {"name": "Blachodachówka", "quantity": 137, "unit": "m²", "price": 6165},
    "counter_battens": {"quantity": 220, "unit": "mb", "price": 1100},
    "battens": {"quantity": 340, "unit": "mb", "price": 1360},
    "membrane": {"quantity": 125, "unit": "m²", "price": 875},
    "screws": {"quantity": 959, "unit": "szt", "price": 290},
    "ridge_tape": {"quantity": 12, "unit": "mb", "price": 180}
  },
  "obstacles": {
    "chimneys": {"quantity": 2, "cost": 100},
    "skylights": {"quantity": 3, "cost": 240}
  },
  "summary": {
    "materials_net": 10310,
    "labor_net": 3609,
    "total_net": 13919,
    "vat": 3201,
    "total_gross": 17120
  }
}
4.6 Generowanie PDF
Template (Jinja2 + WeasyPrint):
html<!DOCTYPE html>
<html>
<head>
  <style>
    /* Firmowe kolory, layout */
  </style>
</head>
<body>
  <!-- NAGŁÓWEK -->
  <div class="header">
    <img src="{{ company_logo }}" />
    <h1>OFERTA NR {{ quote_number }}</h1>
    <p>Data: {{ date }}</p>
  </div>

  <!-- DANE KLIENTA -->
  <div class="client">
    <h2>Dla:</h2>
    <p>{{ client_name }}</p>
    <p>{{ client_address }}</p>
  </div>

  <!-- ZAKRES -->
  <div class="scope">
    <h2>Zakres prac: Wymiana pokrycia dachowego</h2>
    <p>Powierzchnia: {{ real_area }} m²</p>
    <p>Typ dachu: {{ roof_type }}</p>
    <p>Nachylenie: {{ pitch_angle }}°</p>
    <img src="{{ annotated_image }}" />
  </div>

  <!-- ZESTAWIENIE MATERIAŁÓW -->
  <table>
    <thead>
      <tr>
        <th>Poz</th>
        <th>Materiał</th>
        <th>Ilość</th>
        <th>J.m.</th>
        <th>Cena jedn.</th>
        <th>Wartość</th>
      </tr>
    </thead>
    <tbody>
      {% for item in materials %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ item.name }}</td>
        <td>{{ item.quantity }}</td>
        <td>{{ item.unit }}</td>
        <td>{{ item.unit_price }}</td>
        <td>{{ item.total }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <!-- PODSUMOWANIE -->
  <div class="summary">
    <p>Razem netto: {{ total_net }} PLN</p>
    <p>VAT 23%: {{ vat }} PLN</p>
    <h2>RAZEM BRUTTO: {{ total_gross }} PLN</h2>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    <p>Termin realizacji: 14 dni</p>
    <p>Ważność oferty: 30 dni</p>
    <p>Kontakt: {{ salesperson_name }} | {{ salesperson_phone }}</p>
  </div>
</body>
</html>
Backend:
pythonfrom weasyprint import HTML
from django.template.loader import render_to_string

def generate_quote_pdf(quote_id):
    quote = Quote.objects.get(id=quote_id)
    
    context = {
        'quote_number': quote.number,
        'date': quote.created_at.strftime('%d.%m.%Y'),
        'client_name': quote.client_name,
        # ... rest of data
    }
    
    html_string = render_to_string('quote_template.html', context)
    pdf_file = HTML(string=html_string).write_pdf()
    
    # Save to S3
    quote.pdf_url = upload_to_s3(pdf_file, f'quotes/{quote.number}.pdf')
    quote.save()
    
    return quote.pdf_url
4.7 Zarządzanie wycenami
Lista wycen:
javascript// GET /api/quotes/
[
  {
    "id": 145,
    "number": "2026/01/0145",
    "client_name": "Kowalski Jan",
    "total_gross": 17120,
    "status": "sent",
    "created_at": "2026-01-15T14:23:00Z",
    "pdf_url": "https://..."
  },
  // ...
]
Szczegóły wyceny:
javascript// GET /api/quotes/145/
{
  "id": 145,
  "number": "2026/01/0145",
  "client_name": "Kowalski Jan",
  "client_email": "jan@example.com",
  "roof_type": "gable",
  "plan_area": 100.0,
  "real_area": 122.0,
  "pitch_angle": 35,
  "materials": {...},
  "summary": {...},
  "pdf_url": "https://...",
  "status": "sent",
  "created_at": "2026-01-15T14:23:00Z"
}
Statusy:

draft - roboczy
sent - wysłano klientowi
accepted - zaakceptowano
rejected - odrzucono

Akcje:

 Lista wszystkich wycen (filter: status, data)
 Szczegóły wyceny
 Edycja wyceny (powrót do kroku weryfikacji)
 Duplikacja (nowy wariant)
 Pobierz PDF
 Usuń (soft delete)

4.8 Email wysyłka (opcjonalne w MVP, ale nice to have)
Prosty endpoint:
python# POST /api/quotes/{id}/send-email/
{
  "recipient_email": "jan@example.com",
  "message": "Dzień dobry, przesyłam ofertę..."
}

# Backend wysyła email z attachmentem (PDF)

5. MODELE DANYCH
python# users/models.py
class User(AbstractUser):
    role = CharField(max_length=20, choices=[
        ('salesperson', 'Handlowiec'),
        ('manager', 'Manager')
    ])
    company = ForeignKey('Company', on_delete=CASCADE, null=True)

class Company(models.Model):
    name = CharField(max_length=200)
    nip = CharField(max_length=20)
    logo_url = URLField(null=True, blank=True)
    settings = JSONField(default=dict)  
    # settings: {"default_margin": 35, "default_vat": 23}

# materials/models.py
class Material(models.Model):
    CATEGORIES = [
        ('metal_tile', 'Blachodachówka'),
        ('ceramic', 'Dachówka ceramiczna'),
        ('bitumen', 'Papa'),
        ('metal_sheet', 'Blacha trapezowa')
    ]
    
    name = CharField(max_length=200)
    category = CharField(max_length=50, choices=CATEGORIES)
    price_per_m2 = DecimalField(max_digits=8, decimal_places=2)
    waste_factor = DecimalField(max_digits=4, decimal_places=2, default=1.12)
    config = JSONField(default=dict)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

# quotes/models.py
class Quote(models.Model):
    ROOF_TYPES = [
        ('gable', 'Dwuspadowy'),
        ('hip', 'Kopertowy'),
        ('mansard', 'Mansardowy'),
        ('flat', 'Płaski')
    ]
    
    STATUSES = [
        ('draft', 'Roboczy'),
        ('sent', 'Wysłano'),
        ('accepted', 'Zaakceptowano'),
        ('rejected', 'Odrzucono')
    ]
    
    # Meta
    number = CharField(max_length=50, unique=True)  # 2026/01/0123
    user = ForeignKey(User, on_delete=CASCADE)
    status = CharField(max_length=20, choices=STATUSES, default='draft')
    
    # Klient
    client_name = CharField(max_length=200)
    client_email = EmailField(null=True, blank=True)
    client_address = TextField(null=True, blank=True)
    
    # Dach
    roof_type = CharField(max_length=20, choices=ROOF_TYPES)
    plan_area = DecimalField(max_digits=10, decimal_places=2)
    real_area = DecimalField(max_digits=10, decimal_places=2)
    pitch_angle = IntegerField()  # stopnie
    
    # Wymiary (JSON dla prostoty)
    dimensions = JSONField(default=dict)
    # {"length": 12.5, "width": 8.0, "unit": "m"}
    
    # Przeszkody
    obstacles = JSONField(default=list)
    # [{"type": "chimney", "quantity": 2, "cost": 100}, ...]
    
    # AI data
    original_image_url = URLField()
    processed_image_url = URLField(null=True, blank=True)
    ai_extracted_data = JSONField(null=True, blank=True)
    ai_confidence = FloatField(null=True, blank=True)
    
    # Materiały (snapshot na moment tworzenia)
    material = ForeignKey(Material, on_delete=SET_NULL, null=True)
    materials_breakdown = JSONField(default=dict)
    # Pełne rozpisanie jak w przykładzie powyżej
    
    # Finanse
    total_net = DecimalField(max_digits=10, decimal_places=2)
    total_gross = DecimalField(max_digits=10, decimal_places=2)
    margin_percent = IntegerField(default=35)
    vat_rate = IntegerField(default=23)
    
    # PDF
    pdf_url = URLField(null=True, blank=True)
    
    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    sent_at = DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
```

---

## 6. API ENDPOINTS

### 6.1 Auth
```
POST   /api/auth/register/          # Rejestracja
POST   /api/auth/login/             # Login (zwraca JWT)
POST   /api/auth/refresh/           # Refresh token
POST   /api/auth/password-reset/    # Request reset
POST   /api/auth/password-reset-confirm/ # Confirm reset
```

### 6.2 Quotes (główne flow)
```
GET    /api/quotes/                 # Lista wycen (filter, pagination)
POST   /api/quotes/                 # Utwórz nową (tylko meta)
GET    /api/quotes/{id}/            # Szczegóły
PATCH  /api/quotes/{id}/            # Update (edycja)
DELETE /api/quotes/{id}/            # Usuń

POST   /api/quotes/{id}/upload/     # Upload zdjęcia
POST   /api/quotes/{id}/process/    # Trigger AI (Celery task)
GET    /api/quotes/{id}/status/     # Status przetwarzania AI
POST   /api/quotes/{id}/calculate/  # Kalkulacja materiałów
POST   /api/quotes/{id}/generate-pdf/ # Generuj PDF
POST   /api/quotes/{id}/send-email/ # Wyślij email (opcjonalne)
POST   /api/quotes/{id}/duplicate/  # Duplikuj (nowy wariant)
```

### 6.3 Materials
```
GET    /api/materials/              # Lista materiałów (tylko active)
GET    /api/materials/{id}/         # Szczegóły
```

### 6.4 Company (admin tylko)
```
GET    /api/company/settings/       # Ustawienia firmy
PATCH  /api/company/settings/       # Update ustawień

7. FRONTEND - STRUKTURA STRON
7.1 Routing
javascript/login                    → LoginPage
/register                 → RegisterPage

/                         → Dashboard (redirect to /quotes)
/quotes                   → QuotesList
/quotes/new               → NewQuoteFlow
/quotes/:id               → QuoteDetail
/quotes/:id/edit          → EditQuoteFlow (reuse NewQuoteFlow)

/settings                 → UserSettings (opcjonalne)
7.2 NewQuoteFlow - multi-step
Step 1: Upload
javascript<UploadStep>
  <FileDropzone 
    accept="image/*, .pdf"
    maxSize={10 * 1024 * 1024}
    onUpload={handleUpload}
  />
  <LoadingSpinner if={uploading} />
</UploadStep>
Step 2: AI Processing
javascript<ProcessingStep>
  <ProgressBar steps={[
    'Uploading...',
    'Analyzing image...',
    'Extracting dimensions...',
    'Done!'
  ]} />
  
  {/* Polling /api/quotes/{id}/status/ co 2 sekundy */}
</ProcessingStep>
Step 3: Verification
javascript<VerificationStep quote={quote}>
  <ImageCanvas
    imageUrl={quote.original_image_url}
    dimensions={quote.dimensions}
    onDimensionEdit={handleEdit}
  />
  
  <DimensionsForm
    length={quote.dimensions.length}
    width={quote.dimensions.width}
    onChange={handleDimensionsChange}
  />
  
  <PitchAngleInput
    angle={quote.pitch_angle}
    onChange={handlePitchChange}
    presets={[25, 35, 45]}
  />
  
  <ObstaclesManager
    obstacles={quote.obstacles}
    onAdd={handleAddObstacle}
    onRemove={handleRemoveObstacle}
  />
  
  <Button onClick={confirmAndNext}>Dalej →</Button>
</VerificationStep>
Step 4: Material Selection
javascript<MaterialSelectionStep>
  <MaterialGrid materials={materials}>
    {materials.map(m => (
      <MaterialCard
        key={m.id}
        material={m}
        selected={m.id === selectedMaterial}
        onClick={() => selectMaterial(m.id)}
      />
    ))}
  </MaterialGrid>
  
  <LivePreview>
    <p>Powierzchnia: {calculation.real_area} m²</p>
    <p>Materiał potrzebny: {calculation.material_needed} m²</p>
    <p>Szacunkowy koszt: {calculation.total_gross} PLN</p>
  </LivePreview>
  
  <Button onClick={calculate}>Oblicz szczegółowo</Button>
</MaterialSelectionStep>
Step 5: Calculation Result
javascript<CalculationStep quote={quote}>
  <MaterialsBreakdown materials={quote.materials_breakdown} />
  
  <SummaryCard
    materialsNet={quote.summary.materials_net}
    laborNet={quote.summary.labor_net}
    totalNet={quote.summary.total_net}
    vat={quote.summary.vat}
    totalGross={quote.summary.total_gross}
  />
  
  <Button onClick={goToClientData}>Dalej →</Button>
</CalculationStep>
Step 6: Client Data & PDF
javascript<ClientDataStep quote={quote}>
  <Form onSubmit={generatePDF}>
    <Input name="client_name" label="Imię i nazwisko" required />
    <Input name="client_email" label="Email" type="email" />
    <Textarea name="client_address" label="Adres" />
    
    <Button type="submit" loading={generating}>
      Generuj ofertę PDF
    </Button>
  </Form>
  
  {quote.pdf_url && (
    <PDFPreview url={quote.pdf_url}>
      <Button onClick={downloadPDF}>Pobierz PDF</Button>
      <Button onClick={sendEmail}>Wyślij mailem</Button>
    </PDFPreview>
  )}
</ClientDataStep>
7.3 Kluczowe komponenty
ImageCanvas.jsx (Konva.js):
javascriptimport { Stage, Layer, Image, Line, Text } from 'react-konva';

function ImageCanvas({ imageUrl, dimensions, onDimensionEdit }) {
  const [image, setImage] = useState(null);
  const [scale, setScale] = useState(1);
  
  useEffect(() => {
    const img = new window.Image();
    img.src = imageUrl;
    img.onload = () => setImage(img);
  }, [imageUrl]);
  
  return (
    <Stage 
      width={800} 
      height={600}
      scaleX={scale}
      scaleY={scale}
      onWheel={handleZoom}
      draggable
    >
      <Layer>
        {image && <Image image={image} />}
        
        {/* Wymiar - długość */}
        <Line
          points={[0, 50, dimensions.length * pixelRatio, 50]}
          stroke="red"
          strokeWidth={2}
        />
        <Text
          text={`${dimensions.length}m`}
          x={dimensions.length * pixelRatio / 2}
          y={30}
          fontSize={16}
          fill="red"
          onClick={() => onDimensionEdit('length')}
        />
        
        {/* Similar for width */}
      </Layer>
    </Stage>
  );
}
MaterialCard.jsx:
javascriptfunction MaterialCard({ material, selected, onClick }) {
  return (
    <div 
      className={`
        border-2 rounded-lg p-4 cursor-pointer
        ${selected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}
      `}
      onClick={onClick}
    >
      <h3 className="font-bold text-lg">{material.name}</h3>
      <p className="text-gray-600">{material.category_display}</p>
      <p className="text-xl font-semibold mt-2">
        {material.price_per_m2} PLN/m²
      </p>
      {selected && <span className="text-blue-500">✓ Wybrano</span>}
    </div>
  );
}

8. BEZPIECZEŃSTWO I WALIDACJE
8.1 Backend walidacje
python# quotes/validators.py

def validate_dimensions(length, width):
    if length < 2 or length > 50:
        raise ValidationError("Długość musi być 2-50m")
    if width < 2 or width > 30:
        raise ValidationError("Szerokość musi być 2-30m")

def validate_pitch_angle(angle):
    if angle < 3 or angle > 70:
        raise ValidationError("Kąt nachylenia musi być 3-70°")

def validate_file_upload(file):
    # Sprawdź typ MIME
    allowed = ['image/jpeg', 'image/png', 'application/pdf']
    if file.content_type not in allowed:
        raise ValidationError("Niedozwolony typ pliku")
    
    # Sprawdź rozmiar
    if file.size > 10 * 1024 * 1024:
        raise ValidationError("Plik zbyt duży (max 10 MB)")
8.2 Permissions
python# quotes/permissions.py

class IsOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        # User może edytować tylko swoje wyceny
        if request.user.role == 'manager':
            return True
        return obj.user == request.user
8.3 CORS
python# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev
    "https://yourdomain.com"  # Production
]

9. DEPLOYMENT
9.1 Docker Setup
docker-compose.yml:
yamlversion: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: roofquotes
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/roofquotes
      - REDIS_URL=redis://redis:6379/0
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}

  celery:
    build: ./backend
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 9.2 Environment variables

**Backend (.env):**
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
CLAUDE_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=roofquotes
AWS_S3_REGION_NAME=eu-central-1
```

**Frontend (.env):**
```
REACT_APP_API_URL=https://api.yourdomain.com

10. KRYTERIA AKCEPTACJI MVP
Funkcjonalne:

 User może zarejestrować się i zalogować
 User może uploadować zdjęcie/PDF rzutu dachu
 AI przetwarza obraz w < 10 sekund
 User może zweryfikować i edytować wymiary
 User może wybrać materiał z 5 presetów
 System kalkuluje materiały automatycznie
 System generuje profesjonalne PDF
 User może pobrać PDF
 User może przeglądać listę swoich wycen
 Manager może przeglądać wszystkie wyceny

Niefunkcjonalne:

 AI accuracy > 75% dla prostych dachów
 Średni czas wyceny < 4 minuty (user test)
 Aplikacja działa na mobile (responsive)
 API response time < 500ms (p95)
 Brak critical bugs
 Kod pokryty testami (min 60%)

User Experience:

 Prosty, intuicyjny UI (max 1 akcja na ekran)
 Loading states wszędzie gdzie async
 Error handling (jasne komunikaty)
 Mobile-friendly (touch gestures)


11. NICE TO HAVE (ale nie MVP)
Jeśli zostanie czas lub w iteracji 2:

 Email wysyłka z aplikacji
 Wersjonowanie ofert (warianty)
 Panel admin (CRUD materiałów)
 Import cennika z Excela
 Raporty i statystyki
 Duplikacja wycen
 Wyszukiwanie/filtrowanie wycen
 Export do Excela
 Multi-page PDF support (auto-detect przekroju)
 Offline mode (PWA)


12. TIMELINE MVP (orientacyjny)
Tydzień 1-2: Foundation

Setup projektu (Django + React)
Database models
Auth (JWT)
Basic UI scaffolding
File upload do S3

Tydzień 3-4: AI Integration

Claude API integration
Image preprocessing (OpenCV)
Celery setup
AI extraction logic
Error handling

Tydzień 5-6: Verification & Calculation

Konva.js canvas
Inline editing
Material presets (fixtures)
Kalkulacja algorytm
Live updates

Tydzień 7-8: PDF & Polish

WeasyPrint templates
PDF generation
Lista wycen
Bug fixing
User testing
Deploy

Total: 6-8 tygodni

PODSUMOWANIE
Kluczowe założenia:

Hybrid approach - AI ekstrahuje, człowiek weryfikuje
Mobile-first - 80% użycia to telefon
Speed over perfection - 75% accuracy OK, important jest szybkość
Iteracyjne doskonalenie - MVP obsługuje 80% przypadków

Success metrics:

Czas wyceny: 10 min → 2-3 min (70-80% redukcja)
AI accuracy: > 75%
User satisfaction: > 4/5

Tech priorities:

Backend: Stabilność, walidacje, security
Frontend: UX, responsywność, loading states
AI: Accuracy, error handling, fallbacks