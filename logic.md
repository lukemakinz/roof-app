# Logika Analizy i Kalkulacji Dachu

## Spis Treści
1. [Przegląd Systemu](#przegląd-systemu)
2. [Analiza AI (Vision)](#analiza-ai-vision)
3. [Logika Kalkulacji](#logika-kalkulacji)
4. [Elementy Dachowe](#elementy-dachowe)
5. [Przepływ Danych](#przepływ-danych)

---

## Przegląd Systemu

System wyceny dachów wykorzystuje model **OpenAI GPT-4o Vision** do automatycznej analizy rzutów dachów i ekstrakcji wszystkich pomiarów niezbędnych do wyceny materiałów dekarskich.

### Główne Komponenty:
- `ai_processor.py` - analiza obrazu przez AI
- `calculator.py` - kalkulacja materiałów i kosztów
- `views.py` - obsługa żądań API
- `models.py` - model danych Quote

---

## Analiza AI (Vision)

### Model i Konfiguracja

```python
model = "gpt-4o"
temperature = 0          # Maksymalna precyzja
max_tokens = 1024
detail = "high"          # Wysoka rozdzielczość analizy obrazu
```

### Prompt AI

Prompt instruuje model AI jak ekspert dekarski. Główne zasady:

#### Odczyt Wymiarów z Polskich Rysunków:
- Numery na rysunku są w **CENTYMETRACH** (np. 2376 = 23.76m)
- Dzielenie przez 100 daje metry
- Szukanie NAJWIĘKSZYCH wymiarów = wymiary całkowite budynku
- Kąt nachylenia oznaczony jako "25°" lub "30°" na liniach połaci

### Wymagane Pomiary

#### 1. Powierzchnie i Długości Podstawowe
| Parametr | Opis |
|----------|------|
| `powierzchnia_dachu_m2` | Całkowita powierzchnia połaci |
| `dlugosc_krawedzi_szczytowych_lewych_m` | Boczne krawędzie po lewej stronie |
| `dlugosc_krawedzi_szczytowych_prawych_m` | Boczne krawędzie po prawej stronie |
| `dlugosc_kalenic_m` | Górne krawędzie gdzie spotykają się połacie |
| `dlugosc_koszy_m` | Wewnętrzne "doliny" między połaciami |
| `dlugosc_okapow_m` | Dolne krawędzie dachu |

#### 2. Elementy Gąsiorowe
| Element | Opis |
|---------|------|
| `trojniki_szt` | Łączące 3 gąsiory na przecięciach kalenic |
| `gasiory_narozne_szt` | Na narożach/koszach |
| `gasiory_poczatkowe_szt` | Start linii przy okapie |
| `gasiory_koncowe_szt` | Zakończenie przy szczycie |

#### 3. Elementy Dodatkowe
| Element | Opis |
|---------|------|
| `kominy_szt` | Kominy dymowe/spalinowe |
| `kominki_wentylacyjne_szt` | Małe elementy wentylacji |
| `okna_dachowe_szt` | Okna dachowe/świetliki |
| `wylazy_dachowe_szt` | Wyłazy na dach |

#### 4. System Odwodnienia
| Element | Opis |
|---------|------|
| `narozniki_rynien_szt` | Narożniki systemu rynnowego |
| `rury_spustowe_szt` | ~1 na 50-80 m² połaci |
| `zaslepki_rynien_szt` | Zamknięcia końców rynien |

### Format Odpowiedzi AI (JSON)

```json
{
    "typ_dachu": "dwuspadowy|czterospadowy|wielospadowy|kopertowy|mansardowy",
    "kat_nachylenia": 25,
    "wymiary_budynku": {
        "dlugosc_m": 15.89,
        "szerokosc_m": 23.76
    },
    "pomiary": {
        "powierzchnia_dachu_m2": 420,
        "dlugosc_kalenic_m": 12.0,
        "dlugosc_koszy_m": 6.0,
        "dlugosc_okapow_m": 45.0
    },
    "elementy_gasiorowe": {
        "trojniki_szt": 2,
        "gasiory_narozne_szt": 4
    },
    "elementy_dodatkowe": {
        "kominy_szt": 1,
        "kominki_wentylacyjne_szt": 3
    },
    "system_odwodnienia": {
        "rury_spustowe_szt": 6
    },
    "pewnosc_oszacowania": "niska|srednia|wysoka",
    "uwagi": "dodatkowe obserwacje"
}
```

---

## Logika Kalkulacji

### Wzory Powierzchni

```
powierzchnia_rzutu = długość × szerokość

powierzchnia_rzeczywista = powierzchnia_rzutu / cos(kąt_nachylenia)
```

### Przeliczniki dla Kątów Nachylenia

| Kąt | Mnożnik |
|-----|---------|
| 25° | 1.10 |
| 30° | 1.15 |
| 35° | 1.22 |
| 45° | 1.41 |

### Kalkulacja Materiałów

#### 1. Pokrycie Dachowe
```
materiał_potrzebny = powierzchnia_rzeczywista × współczynnik_odpadu

współczynnik_odpadu = 1.12 (12% na przycięcia i odpady)
```

#### 2. Łaty i Kontrłaty
```
wysokość_dachu = (szerokość / 2) × tan(kąt)
długość_krokwi = √((szerokość/2)² + wysokość²)
ilość_rzędów_łat = (długość_krokwi × 100) / rozstaw_łat_cm + 1
metry_łat = ilość_rzędów × długość × 2  // obie strony dachu
```

#### 3. Membrana Dachowa
```
powierzchnia_membrany = powierzchnia_rzeczywista × 1.05  // 5% zakład
```

#### 4. Wkręty
```
ilość_wkrętów = materiał_potrzebny × wkręty_na_m²
```

### Koszty Obróbek Przeszkód

| Typ Przeszkody | Redukcja Pow. | Koszt Obróbki |
|----------------|---------------|---------------|
| Komin | -1.0 m² | 50 PLN |
| Okno dachowe | -0.5 m² | 80 PLN |
| Wyłaz dachowy | -0.8 m² | 40 PLN |
| Kominek wentylacyjny | -0.1 m² | 35 PLN |

### Podsumowanie Kosztów

```
materiały_netto = pokrycie + łaty + kontrłaty + membrana + wkręty + taśma + obróbki

robocizna = materiały_netto × marża%

razem_netto = materiały_netto + robocizna
VAT = razem_netto × stawka_VAT%
razem_brutto = razem_netto + VAT
```

---

## Elementy Dachowe

### Typy Dachów

| Typ | Polski | Opis |
|-----|--------|------|
| `gable` | Dwuspadowy | Dwie połacie nachylone w przeciwnych kierunkach |
| `hip` | Kopertowy/Czterospadowy | Cztery połacie opadające do okapu |
| `mansard` | Mansardowy | Dach z załamaniem - górna część łagodniejsza |
| `flat` | Płaski | Minimalny kąt nachylenia |

### Krawędzie Dachu

```
┌─────────────────────────┐
│         KALENICA        │  ← Górna krawędź (ridge)
│    ╱            ╲       │
│   ╱              ╲      │
│  ╱                ╲     │
│ ╱  KOSZ (valley)   ╲    │  ← Wewnętrzna wklęsła krawędź
│╱____________________╲   │
│        OKAP             │  ← Dolna krawędź (eave)
└─────────────────────────┘
 ↑                      ↑
SZCZYT                SZCZYT
(gable edge)       (gable edge)
```

---

## Przepływ Danych

### 1. Upload Obrazu
```
Użytkownik → POST /api/quotes/{id}/upload/ → Zapis obrazu
```

### 2. Analiza AI
```
POST /api/quotes/{id}/process/
    ↓
ai_processor.process_roof_image()
    ↓
OpenAI GPT-4o Vision API
    ↓
Parsowanie JSON → Zapis do Quote model
```

### 3. Mapowanie Odpowiedzi AI → Model

```python
# Typ dachu (Polish → English)
roof_type_map = {
    'dwuspadowy': 'gable',
    'czterospadowy': 'hip',
    'wielospadowy': 'hip',
    'kopertowy': 'hip',
    'mansardowy': 'mansard'
}

# Zapisywane pola
quote.dimensions = {'length': X, 'width': Y}
quote.roof_measurements = {ridges, valleys, eaves}
quote.gasior_elements = {junctions, corners, start, end}
quote.gutter_system = {corners, downpipes, end_caps}
quote.obstacles = [{type, quantity}, ...]
```

### 4. Kalkulacja
```
POST /api/quotes/{id}/calculate/
    ↓
calculator.calculate_roof_materials(quote, material)
    ↓
Wyliczenie wszystkich materiałów i kosztów
    ↓
Zapis do Quote: materials_breakdown, total_net, total_gross
```

### 5. Generowanie PDF
```
POST /api/quotes/{id}/generate_pdf/
    ↓
pdf_generator.generate_quote_pdf(quote)
    ↓
Zapis PDF → quote.pdf_file
```

---

## Koszty API

### Szacunkowe Zużycie Tokenów (1 analiza):

| Składnik | Tokeny |
|----------|--------|
| Prompt | ~900 |
| Obraz (high detail) | ~2000 |
| Odpowiedź JSON | ~400 |
| **RAZEM** | ~3300 |

### Koszt:
- ~$0.01 za analizę (~4-5 groszy PLN)
- ~$10 za 1000 analiz (~40 PLN)
