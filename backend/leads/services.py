"""
AI processor service for leads - extracting roof dimensions from images using OpenAI Vision.
Based on the working code from quotes/services/ai_processor.py
"""
import os
import io
import json
import re
import math
import base64
import logging
from typing import Optional
from pathlib import Path

from django.conf import settings
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def register_polish_fonts():
    """Register fonts with Polish character support."""
    font_paths = [
        # macOS
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/Library/Fonts/Arial Unicode.ttf',
        # Common DejaVu locations
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('PolishFont', font_path))
                logger.info(f"Registered Polish font from: {font_path}")
                return 'PolishFont'
            except Exception as e:
                logger.warning(f"Failed to register font {font_path}: {e}")

    logger.warning("No Polish font found, using Helvetica")
    return 'Helvetica'


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(image_file.read()).decode("utf-8")


def get_image_media_type(file_path: str) -> str:
    """Get the media type based on file extension."""
    extension = Path(file_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
    }
    return media_types.get(extension, 'image/jpeg')


# ============================================
# VALIDATION FUNCTIONS (from ai_processor.py)
# ============================================

def validate_dimensions(data: dict) -> dict:
    """
    Validate and correct dimension reading from AI.
    Uses raw values (wymiary_surowe) to recalculate if needed.
    """
    validation_warnings = data.get('validation_warnings', [])

    # RULE 0: Validate and fix angle (kat_nachylenia)
    kat = data.get('kat_nachylenia', 0)
    # Handle case where AI returned a string instead of number
    if isinstance(kat, str):
        match = re.search(r'(\d+)', str(kat))
        if match:
            kat = int(match.group(1))
            validation_warnings.append(f"Kąt nachylenia wyekstrahowany z tekstu: {kat}°")
        else:
            kat = 0

    # If angle is 0 or unrealistic, add warning
    if kat == 0:
        validation_warnings.append("UWAGA: Kąt nachylenia nie został znaleziony na rysunku - wymaga ręcznej weryfikacji")
        data['kat_nachylenia'] = 0
    elif kat < 5 or kat > 60:
        validation_warnings.append(f"UWAGA: Kąt nachylenia {kat}° poza typowym zakresem (5-60°) - wymaga weryfikacji")
        data['kat_nachylenia'] = kat
    else:
        data['kat_nachylenia'] = kat

    wymiary_surowe = data.get('wymiary_surowe', {})
    wymiary = data.get('wymiary_budynku', {})

    dlugosc_cm = wymiary_surowe.get('dlugosc_cm', 0)
    szerokosc_cm = wymiary_surowe.get('szerokosc_cm', 0)
    dlugosc_m = wymiary.get('dlugosc_m', 0)
    szerokosc_m = wymiary.get('szerokosc_m', 0)

    # RULE 1: If raw values exist, recalculate from them (they should be in cm)
    if dlugosc_cm > 0 and szerokosc_cm > 0:
        # Check if raw values look like millimeters (>10000) vs centimeters
        if dlugosc_cm > 10000:
            corrected_dlugosc = dlugosc_cm / 1000
            validation_warnings.append(f"Wymiar {dlugosc_cm} interpretowany jako mm → {corrected_dlugosc}m")
        else:
            corrected_dlugosc = dlugosc_cm / 100

        if szerokosc_cm > 10000:
            corrected_szerokosc = szerokosc_cm / 1000
            validation_warnings.append(f"Wymiar {szerokosc_cm} interpretowany jako mm → {corrected_szerokosc}m")
        else:
            corrected_szerokosc = szerokosc_cm / 100

        # Update if different from AI calculation
        if abs(corrected_dlugosc - dlugosc_m) > 0.1:
            validation_warnings.append(f"Skorygowano długość: {dlugosc_m}m → {corrected_dlugosc}m")
            wymiary['dlugosc_m'] = corrected_dlugosc

        if abs(corrected_szerokosc - szerokosc_m) > 0.1:
            validation_warnings.append(f"Skorygowano szerokość: {szerokosc_m}m → {corrected_szerokosc}m")
            wymiary['szerokosc_m'] = corrected_szerokosc

    # RULE 2: Validate final dimensions are in realistic range
    dlugosc_m = wymiary.get('dlugosc_m', 0)
    szerokosc_m = wymiary.get('szerokosc_m', 0)

    if dlugosc_m < 5 or dlugosc_m > 35:
        validation_warnings.append(f"UWAGA: Długość {dlugosc_m}m poza typowym zakresem (5-35m) - wymaga weryfikacji")

    if szerokosc_m < 5 or szerokosc_m > 35:
        validation_warnings.append(f"UWAGA: Szerokość {szerokosc_m}m poza typowym zakresem (5-35m) - wymaga weryfikacji")

    # RULE 3: Recalculate surface area based on corrected dimensions
    if dlugosc_m > 0 and szerokosc_m > 0:
        pomiary = data.get('pomiary', {})
        plan_area = dlugosc_m * szerokosc_m
        kat_dla_obliczen = data.get('kat_nachylenia', 0)

        if kat_dla_obliczen == 0:
            kat_dla_obliczen = 30  # Conservative estimate for calculations only
            validation_warnings.append("Do obliczeń powierzchni użyto domyślnego kąta 30° (brak danych)")

        real_area = plan_area / math.cos(math.radians(kat_dla_obliczen)) if kat_dla_obliczen > 0 else plan_area

        old_area = pomiary.get('powierzchnia_dachu_m2', 0)
        if abs(real_area - old_area) > 20:
            validation_warnings.append(f"Przeliczono powierzchnię: {old_area}m² → {round(real_area, 1)}m²")
            pomiary['powierzchnia_dachu_m2'] = round(real_area, 1)

        data['pomiary'] = pomiary

    data['wymiary_budynku'] = wymiary
    if validation_warnings:
        data['validation_warnings'] = validation_warnings

    return data


def validate_ai_response(data: dict) -> dict:
    """
    Post-processing validation and correction of AI response.
    Fixes common hallucination issues and applies logical rules.
    """
    validation_warnings = data.get('validation_warnings', [])

    elementy = data.get('elementy_dodatkowe', {})
    pomiary = data.get('pomiary', {})
    rynny = data.get('system_odwodnienia', {})
    pewnosc = data.get('pewnosc_oszacowania', 'srednia')
    elementy_niepewne = data.get('elementy_niepewne', [])

    kominy = elementy.get('kominy_szt', 0)
    kominki = elementy.get('kominki_wentylacyjne_szt', 0)
    okna = elementy.get('okna_dachowe_szt', 0)
    wylazy = elementy.get('wylazy_dachowe_szt', 0)
    okapy = pomiary.get('dlugosc_okapow_m', 0)

    # RULE 0: Sanity check - total elements
    total_elements = kominy + kominki + okna + wylazy
    if total_elements > kominy + 2:
        validation_warnings.append(
            f"UWAGA: Suma elementów ({total_elements}) wydaje się za wysoka - możliwe podwójne liczenie"
        )

    # RULE 1: Low/medium confidence = be very conservative with rare elements
    if pewnosc in ['niska', 'srednia']:
        if okna > 0:
            validation_warnings.append(f"Przy pewności '{pewnosc}' wyzerowano okna dachowe (było: {okna})")
            elementy['okna_dachowe_szt'] = 0
        if wylazy > 0:
            validation_warnings.append(f"Przy pewności '{pewnosc}' wyzerowano wyłazy dachowe (było: {wylazy})")
            elementy['wylazy_dachowe_szt'] = 0
        if kominki > 0:
            validation_warnings.append(f"Przy pewności '{pewnosc}' wyzerowano kominki wentylacyjne (było: {kominki})")
            elementy['kominki_wentylacyjne_szt'] = 0

    # RULE 2: Even with high confidence, apply strict limits
    if kominy > 4:
        validation_warnings.append(f"Skorygowano liczbę kominów z {kominy} do 4")
        elementy['kominy_szt'] = 4

    if okna > 2:
        validation_warnings.append(f"Skorygowano liczbę okien dachowych z {okna} do 2")
        elementy['okna_dachowe_szt'] = 2

    if wylazy > 1:
        validation_warnings.append(f"Skorygowano liczbę wyłazów z {wylazy} do 1")
        elementy['wylazy_dachowe_szt'] = 1

    if kominki > 2:
        validation_warnings.append(f"Skorygowano liczbę kominków wentylacyjnych z {kominki} do 2")
        elementy['kominki_wentylacyjne_szt'] = 2

    # RULE 3: If element is in "uncertain" list, zero it
    elementy_niepewne_lower = [e.lower() for e in elementy_niepewne]
    if any('okn' in e or 'świetl' in e for e in elementy_niepewne_lower):
        if elementy.get('okna_dachowe_szt', 0) > 0:
            validation_warnings.append("Wyzerowano okna dachowe - były na liście niepewnych elementów")
            elementy['okna_dachowe_szt'] = 0
    if any('wyłaz' in e or 'właz' in e for e in elementy_niepewne_lower):
        if elementy.get('wylazy_dachowe_szt', 0) > 0:
            validation_warnings.append("Wyzerowano wyłazy - były na liście niepewnych elementów")
            elementy['wylazy_dachowe_szt'] = 0
    if any('went' in e for e in elementy_niepewne_lower):
        if elementy.get('kominki_wentylacyjne_szt', 0) > 0:
            validation_warnings.append("Wyzerowano kominki wentylacyjne - były na liście niepewnych elementów")
            elementy['kominki_wentylacyjne_szt'] = 0

    # RULE 4: Auto-fill gutter system if missing but eaves present
    if okapy > 0:
        if rynny.get('rury_spustowe_szt', 0) == 0:
            expected_rury = max(2, int(okapy / 10))
            rynny['rury_spustowe_szt'] = expected_rury
            validation_warnings.append(f"Auto-uzupełniono rury spustowe: {expected_rury} szt.")

    data['elementy_dodatkowe'] = elementy
    data['system_odwodnienia'] = rynny
    if validation_warnings:
        data['validation_warnings'] = validation_warnings

    return data


def validate_roof_type_consistency(data: dict) -> dict:
    """
    Cross-validation: check if detected elements are consistent with roof type.
    """
    typ = data.get('typ_dachu', '').lower()
    pomiary = data.get('pomiary', {})
    gasiory = data.get('elementy_gasiorowe', {})

    kosze = pomiary.get('dlugosc_koszy_m', 0)
    trojniki = gasiory.get('trojniki_szt', 0)
    kalenice = pomiary.get('dlugosc_kalenic_m', 0)

    validation_warnings = data.get('validation_warnings', [])

    if typ == 'dwuspadowy' and (kosze > 0 or trojniki > 0):
        validation_warnings.append(
            f"Typ '{typ}' nie powinien mieć koszy ({kosze}m) ani trójników ({trojniki}szt) - prawdopodobnie wielospadowy"
        )
        if kosze > 0:
            data['typ_dachu'] = 'wielospadowy'

    if typ in ['jednospadowy', 'pulpitowy']:
        if kalenice > 0:
            pomiary['dlugosc_kalenic_m'] = 0
            validation_warnings.append(f"Wyzerowano kalenice dla dachu {typ}")
        if trojniki > 0:
            gasiory['trojniki_szt'] = 0

    if typ == 'plaski':
        if data.get('kat_nachylenia', 0) > 10:
            validation_warnings.append(
                f"Dach płaski z kątem {data.get('kat_nachylenia')}° - możliwa pomyłka typu"
            )

    data['pomiary'] = pomiary
    data['elementy_gasiorowe'] = gasiory
    if validation_warnings:
        data['validation_warnings'] = validation_warnings

    return data


# ============================================
# MAIN PROCESSING FUNCTION
# ============================================

def process_roof_image(file_path: str) -> Optional[dict]:
    """
    Process roof image using OpenAI Vision API to extract dimensions.
    Uses a two-step approach for better accuracy.

    Returns:
        dict with extracted data or None if processing failed
    """
    try:
        logger.info(f"Processing image: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        file_size = os.path.getsize(file_path)
        logger.info(f"DEBUG: Image file size: {file_size} bytes")
        if file_size == 0:
            logger.error("DEBUG: File is empty!")
            return None

        # Encode image
        image_data = encode_image_to_base64(file_path)
        media_type = get_image_media_type(file_path)
        logger.info(f"DEBUG: Media type: {media_type}")
        
        if not settings.OPENAI_API_KEY:
            logger.error("DEBUG: OPENAI_API_KEY is missing!")
            return None
            
        logger.info(f"DEBUG: Using API Key: {settings.OPENAI_API_KEY[:5]}...")

        # STEP 1: First, extract ONLY the angle with a focused query
        angle_prompt = """Przeanalizuj ten rysunek techniczny dachu.

TWOJE JEDYNE ZADANIE: Znajdź kąt nachylenia dachu.

WAŻNE - Na polskich rysunkach technicznych kąt nachylenia jest często oznaczony:
- Małym łukiem ze strzałką przy linii ukośnej dachu
- Liczba może być napisana OBOK łuku (np. "40" obok małego łuku ze strzałką)
- Czasem wygląda jak ".40" lub "40." z łukiem
- Symbol ° (stopni) może być pominięty
- Strzałka wskazuje kierunek spadku

Szukaj w tych miejscach:
- Przy linii ukośnej reprezentującej połać dachu
- W przekrojach A-A, B-B
- W widoku elewacji (bok budynku)
- Przy krawędzi dachu gdzie widać spadek

Patrz na KAŻDĄ liczbę dwucyfrową (jak 40, 35, 25, 45) która jest blisko:
- Małego łuku lub półkola
- Strzałki wskazującej kierunek
- Linii ukośnej dachu

Odpowiedz TYLKO jedną liczbą - wartość kąta którą widzisz.
Jeśli widzisz liczbę "40" przy łuku/strzałce - odpowiedz: 40
Jeśli widzisz "35" przy linii dachu - odpowiedz: 35
Jeśli nie ma kąta - odpowiedz: 0

ODPOWIEDŹ (tylko liczba):"""

        try:
            angle_response = client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": angle_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}",
                                    "detail": "high"
                                }
                            }
                        ],
                    }
                ],
                max_tokens=50,
                temperature=0,
            )

            angle_text = angle_response.choices[0].message.content.strip()
            logger.info(f"Angle extraction response: '{angle_text}'")

            angle_match = re.search(r'(\d+)', angle_text)
            extracted_angle = int(angle_match.group(1)) if angle_match else 0
            logger.info(f"Extracted angle: {extracted_angle}")

        except Exception as e:
            logger.error(f"Angle extraction failed: {e}")
            extracted_angle = 0

        # STEP 2: Main analysis with the extracted angle hint
        system_message = f"""Jesteś precyzyjnym ekspertem od analizy rysunków technicznych dachów.

WAŻNE: Wstępna analiza wykryła kąt nachylenia: {extracted_angle}°
Użyj tej wartości dla kat_nachylenia, chyba że WYRAŹNIE widzisz inną wartość na rysunku.

Jeśli wstępna analiza dała 0, oznacza to że kąt nie został znaleziony - wtedy też wpisz 0."""

        # Enhanced roof analysis prompt
        prompt = """Jesteś ekspertem dekarzem analizującym rzut dachu.

## KRYTYCZNE ZASADY:

### 1. WYMIARY BUDYNKU - NAJWAŻNIEJSZE!

**KROK 1: Znajdź linie wymiarowe na ZEWNĘTRZNYCH krawędziach rysunku**
- Linie wymiarowe mają strzałki lub kreski na końcach
- Szukaj na GÓRNEJ krawędzi = SZEROKOŚĆ budynku
- Szukaj na LEWEJ lub PRAWEJ krawędzi = DŁUGOŚĆ budynku

**KROK 2: Wybierz CAŁKOWITY wymiar (nie segmenty)**
- Całkowity wymiar obejmuje CAŁY budynek
- Ignoruj małe wymiary wewnętrzne (pokoje, segmenty)
- Jeśli są tylko segmenty - zsumuj je

**KROK 3: Konwersja jednostek**
Polskie rysunki używają CENTYMETRÓW:
- 1308 → 1308 cm → 13.08 m
- 1031 → 1031 cm → 10.31 m
- 2376 → 2376 cm → 23.76 m
- 951 → 951 cm → 9.51 m

**KROK 4: Zapisz SUROWE wartości**
Zwróć zarówno wartość surową (w cm) jak i przeliczoną (w m).

**TYPOWE WYMIARY DOMÓW:**
- Małe domy: 8-12m x 8-12m
- Średnie domy: 10-15m x 10-15m
- Duże domy: 12-25m x 12-20m
- Jeśli wymiar > 30m - prawdopodobnie błąd!

### 2. TYLKO TO CO WIDZISZ - NIE DOMYŚLAJ SIĘ!
⚠️ Jeśli elementu NIE WIDZISZ → wpisz 0
⚠️ Lepiej wpisać 0 niż zgadywać!

### 3. IDENTYFIKACJA TYPU DACHU:
| Typ | Cechy charakterystyczne |
|-----|------------------------|
| jednospadowy | Jedna pochyła płaszczyzna, brak kalenicy |
| dwuspadowy | Dwie połacie, kalenica na środku |
| dwuspadowy_l | Dwuspadowy na planie L |
| czterospadowy | 4 połacie opadające do okapów |
| kopertowy | Czterospadowy bez szczytów (koperta) |
| wielospadowy | Więcej niż 4 połacie, złożony kształt |
| wielospadowy_l | Wielospadowy na planie L |
| mansardowy | Załamanie połaci - dwa różne kąty |
| naczolkowy | Dwuspadowy z ściętymi szczytami |
| pulpitowy | Jedna płaska pochyła płaszczyzna |
| plaski | Minimalny lub zerowy kąt nachylenia |

### 4. IDENTYFIKACJA ELEMENTÓW NA RYSUNKU - ULTRA PRECYZYJNIE!

⚠️ ZASADA GŁÓWNA: Domyślnie WSZYSTKIE elementy = 0. Zwiększ tylko jeśli WIDZISZ konkretny element!

**KOMIN dymowy/spalinowy (kominy_szt):**
- JEDYNY sposób identyfikacji: KWADRAT/PROSTOKĄT z KRZYŻEM (X) lub przekątnymi liniami w środku
- Typowy rozmiar: 30-60cm (duży element)
- Może mieć oznaczenie "K", "komin", "K1", "K2"
- ⚠️ Prostokąt BEZ krzyża to NIE JEST komin!
- POLICZ: ile widzisz kwadratów/prostokątów Z KRZYŻEM W ŚRODKU?

**OKNO DACHOWE / ŚWIETLIK (okna_dachowe_szt):**
- JEDYNY sposób identyfikacji: prostokąt Z WYRAŹNYM OZNACZENIEM "OD", "okno", "świetlik", "velux"
- ⚠️ Sam prostokąt bez oznaczenia to NIE JEST okno!
- ⚠️ Prostokąt z krzyżem to KOMIN, nie okno!
- DOMYŚLNIE: 0 (większość dachów nie ma okien dachowych na rzucie!)

**KOMINEK WENTYLACYJNY (kominki_wentylacyjne_szt):**
- JEDYNY sposób identyfikacji: MAŁE KÓŁKO (okrąg) o średnicy ~10-15cm
- Może mieć oznaczenie "KW", "W", "went.", "wentylacja"
- ⚠️ To NIE jest duży kwadrat - to małe kółko!
- DOMYŚLNIE: 0 (kominki wentylacyjne są rzadkie!)

**WYŁAZ DACHOWY (wylazy_dachowe_szt):**
- JEDYNY sposób identyfikacji: mały kwadrat Z WYRAŹNYM OZNACZENIEM "wyłaz", "WD", "właz"
- DOMYŚLNIE: 0 (wyłazy są bardzo rzadkie!)

### TABELA ROZRÓŻNIANIA ELEMENTÓW:
| Element widzę | Ma krzyż X? | Ma oznaczenie? | To jest: |
|---------------|-------------|----------------|----------|
| Duży kwadrat  | TAK         | -              | KOMIN    |
| Duży kwadrat  | NIE         | "OD"/"okno"    | OKNO DACHOWE |
| Duży kwadrat  | NIE         | brak           | IGNORUJ  |
| Małe kółko    | -           | -              | KOMINEK WENTYLACYJNY |
| Mały kwadrat  | NIE         | "wyłaz"/"WD"   | WYŁAZ    |

⚠️ KRYTYCZNE ZASADY:
1. Policz TYLKO elementy które WYRAŹNIE widzisz i możesz zidentyfikować!
2. Kwadrat z X = ZAWSZE KOMIN (nigdy okno!)
3. Jeśli nie jesteś 100% pewien co to jest → wpisz 0
4. NIE ZGADUJ! Lepiej wpisać 0 niż zmyślić element którego nie ma
5. Typowy dom ma 1-2 kominy, 0 okien dachowych, 0 kominków wentylacyjnych, 0 wyłazów

### 5. FORMAT ODPOWIEDZI (TYLKO JSON):

⚠️ KRYTYCZNE: Zwróć TYLKO wartości liczbowe! NIE używaj formuł!
❌ ŹLE: "powierzchnia_dachu_m2": 12.5 * 9.8 * 2 / Math.cos(...)
✅ DOBRZE: "powierzchnia_dachu_m2": 165.2

STRUKTURA JSON:

{
    "typ_dachu": "jednospadowy|dwuspadowy|dwuspadowy_l|czterospadowy|kopertowy|wielospadowy|wielospadowy_l|mansardowy|naczolkowy|pulpitowy|plaski",
    "kat_nachylenia": LICZBA,
    "wymiary_surowe": {
        "dlugosc_cm": LICZBA,
        "szerokosc_cm": LICZBA
    },
    "wymiary_budynku": {
        "dlugosc_m": LICZBA,
        "szerokosc_m": LICZBA
    },
    "pomiary": {
        "powierzchnia_dachu_m2": LICZBA,
        "dlugosc_krawedzi_szczytowych_lewych_m": LICZBA,
        "dlugosc_krawedzi_szczytowych_prawych_m": LICZBA,
        "dlugosc_kalenic_m": LICZBA,
        "dlugosc_koszy_m": LICZBA,
        "dlugosc_okapow_m": LICZBA
    },
    "elementy_gasiorowe": {
        "trojniki_szt": LICZBA,
        "gasiory_narozne_szt": LICZBA,
        "gasiory_poczatkowe_szt": LICZBA,
        "gasiory_koncowe_szt": LICZBA
    },
    "elementy_dodatkowe": {
        "kominy_szt": LICZBA,
        "kominki_wentylacyjne_szt": LICZBA,
        "okna_dachowe_szt": LICZBA,
        "wylazy_dachowe_szt": LICZBA
    },
    "system_odwodnienia": {
        "narozniki_rynien_szt": LICZBA,
        "rury_spustowe_szt": LICZBA,
        "zaslepki_rynien_szt": LICZBA
    },
    "pewnosc_oszacowania": "niska|srednia|wysoka",
    "elementy_niepewne": ["lista elementów niepewnych"],
    "uwagi": "string z uwagami"
}

Zwróć WYŁĄCZNIE poprawny JSON. Żadnych formuł, żadnego kodu, żadnego markdown."""

        # Call OpenAI API for main analysis
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20",
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ],
                }
            ],
            max_tokens=4096,
            temperature=0,
        )

        # Parse response
        response_text = response.choices[0].message.content
        logger.info(f"AI raw response (first 1000 chars): {response_text[:1000] if response_text else 'EMPTY'}")

        if not response_text:
            logger.error("AI returned empty response")
            return None

        # Clean up response
        response_text = response_text.strip()

        if response_text.startswith('```'):
            first_newline = response_text.find('\n')
            if first_newline != -1:
                response_text = response_text[first_newline + 1:]

        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        if not response_text.startswith('{'):
            json_start = response_text.find('{')
            if json_start != -1:
                response_text = response_text[json_start:]

        if not response_text.endswith('}'):
            json_end = response_text.rfind('}')
            if json_end != -1:
                response_text = response_text[:json_end + 1]

        result = json.loads(response_text)

        # Apply post-processing validation (dimensions first!)
        result = validate_dimensions(result)
        result = validate_ai_response(result)
        result = validate_roof_type_consistency(result)

        logger.info(f"Final validated result: {result}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response. Error: {str(e)}")

        # Try to fix common JSON issues
        try:
            if 'response_text' in dir():
                cleaned = re.sub(r'//.*$', '', response_text, flags=re.MULTILINE)
                cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
                result = json.loads(cleaned)

                result = validate_dimensions(result)
                result = validate_ai_response(result)
                result = validate_roof_type_consistency(result)

                return result
        except:
            pass

        return None
    except Exception as e:
        logger.error(f"AI processing error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ============================================
# PDF GENERATION
# ============================================

def generate_result_pdf(lead) -> Optional[bytes]:
    """
    Generate a professionally styled PDF with roof analysis results.
    Returns PDF content as bytes.
    """
    try:
        buffer = io.BytesIO()
        polish_font = register_polish_fonts()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        # Colors
        primary_color = HexColor('#1a365d')
        secondary_color = HexColor('#2d3748')
        accent_color = HexColor('#3182ce')
        success_color = HexColor('#38a169')
        text_color = HexColor('#4a5568')
        light_gray = HexColor('#f7fafc')
        border_color = HexColor('#e2e8f0')

        # Styles
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName=polish_font,
            fontSize=28,
            textColor=primary_color,
            spaceAfter=5,
            alignment=TA_CENTER,
            leading=34
        )

        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName=polish_font,
            fontSize=11,
            textColor=text_color,
            spaceAfter=20,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            fontName=polish_font,
            fontSize=14,
            textColor=primary_color,
            spaceBefore=25,
            spaceAfter=12,
            leading=18
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            fontName=polish_font,
            fontSize=11,
            textColor=text_color,
            spaceAfter=6,
            leading=16
        )

        label_style = ParagraphStyle(
            'Label',
            fontName=polish_font,
            fontSize=10,
            textColor=HexColor('#718096'),
            spaceAfter=2
        )

        value_style = ParagraphStyle(
            'Value',
            fontName=polish_font,
            fontSize=12,
            textColor=secondary_color,
            spaceAfter=10
        )

        price_style = ParagraphStyle(
            'PriceStyle',
            fontName=polish_font,
            fontSize=24,
            textColor=success_color,
            spaceBefore=10,
            spaceAfter=5,
            alignment=TA_CENTER,
            leading=30
        )

        price_label_style = ParagraphStyle(
            'PriceLabel',
            fontName=polish_font,
            fontSize=12,
            textColor=text_color,
            spaceAfter=5,
            alignment=TA_CENTER
        )

        footer_style = ParagraphStyle(
            'Footer',
            fontName=polish_font,
            fontSize=9,
            textColor=HexColor('#a0aec0'),
            alignment=TA_CENTER,
            spaceBefore=20
        )

        # Build content
        content = []

        content.append(Paragraph("WYCENA DACHU", title_style))
        content.append(Paragraph(f"Raport nr: {str(lead.public_uuid)[:8].upper()}", subtitle_style))

        content.append(HRFlowable(
            width="100%",
            thickness=2,
            color=accent_color,
            spaceAfter=20
        ))

        # Add uploaded image
        if lead.uploaded_file and lead.file_type in ['jpg', 'png']:
            try:
                img_path = lead.uploaded_file.path
                if os.path.exists(img_path):
                    with PILImage.open(img_path) as pil_img:
                        img_width, img_height = pil_img.size

                    max_width = 15 * cm
                    max_height = 10 * cm

                    aspect = img_width / img_height
                    if img_width > img_height:
                        width = min(max_width, img_width)
                        height = width / aspect
                        if height > max_height:
                            height = max_height
                            width = height * aspect
                    else:
                        height = min(max_height, img_height)
                        width = height * aspect
                        if width > max_width:
                            width = max_width
                            height = width / aspect

                    content.append(Paragraph("Przeslany rysunek", heading_style))
                    img = Image(img_path, width=width, height=height)
                    content.append(img)
                    content.append(Spacer(1, 15))
            except Exception as e:
                logger.warning(f"Could not add image to PDF: {e}")

        # Contact info
        content.append(Paragraph("Dane kontaktowe", heading_style))

        contact_data = [
            [Paragraph("Email:", label_style), Paragraph(lead.email, value_style)],
            [Paragraph("Telefon:", label_style), Paragraph(lead.phone, value_style)],
        ]

        contact_table = Table(contact_data, colWidths=[3*cm, 13*cm])
        contact_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        content.append(contact_table)

        # Roof analysis results
        content.append(Paragraph("Wyniki analizy", heading_style))

        analysis_data = []
        if lead.roof_type:
            analysis_data.append([
                Paragraph("Typ dachu:", label_style),
                Paragraph(lead.roof_type.capitalize(), value_style)
            ])
        if lead.pitch_angle:
            analysis_data.append([
                Paragraph("Kat nachylenia:", label_style),
                Paragraph(f"{lead.pitch_angle} stopni", value_style)
            ])
        if lead.roof_area:
            analysis_data.append([
                Paragraph("Powierzchnia dachu:", label_style),
                Paragraph(f"{lead.roof_area} m2", value_style)
            ])

        if analysis_data:
            analysis_table = Table(analysis_data, colWidths=[5*cm, 11*cm])
            analysis_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                ('BOX', (0, 0), (-1, -1), 1, border_color),
            ]))
            content.append(analysis_table)

        # Dimensions
        if lead.dimensions:
            content.append(Paragraph("Wymiary", heading_style))
            dims = lead.dimensions
            dim_data = []

            if dims.get('dlugosc_m'):
                dim_data.append([
                    Paragraph("Dlugosc:", label_style),
                    Paragraph(f"{dims['dlugosc_m']} m", value_style)
                ])
            if dims.get('szerokosc_m'):
                dim_data.append([
                    Paragraph("Szerokosc:", label_style),
                    Paragraph(f"{dims['szerokosc_m']} m", value_style)
                ])

            if dim_data:
                dim_table = Table(dim_data, colWidths=[5*cm, 11*cm])
                dim_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ]))
                content.append(dim_table)

        # Roof elements
        if lead.roof_elements:
            content.append(Paragraph("Elementy dachu", heading_style))
            elements = lead.roof_elements
            elem_items = []

            if elements.get('kominy'):
                elem_items.append(f"Kominy: {elements['kominy']}")
            if elements.get('kominki_wentylacyjne'):
                elem_items.append(f"Kominki wentylacyjne: {elements['kominki_wentylacyjne']}")
            if elements.get('okna_dachowe'):
                elem_items.append(f"Okna dachowe: {elements['okna_dachowe']}")
            if elements.get('wylazy_dachowe'):
                elem_items.append(f"Wylazy dachowe: {elements['wylazy_dachowe']}")
            if elements.get('lukarny'):
                elem_items.append(f"Lukarny: {elements['lukarny']}")
            if elements.get('rynny'):
                elem_items.append("Rynny: Tak")

            for item in elem_items:
                content.append(Paragraph(f"  •  {item}", normal_style))

        # Warnings
        if lead.ai_warnings:
            content.append(Paragraph("Uwagi", heading_style))
            for warning in lead.ai_warnings:
                content.append(Paragraph(f"  •  {warning}", normal_style))

        # Price section
        content.append(Spacer(1, 20))

        if lead.estimated_price_min:
            price_box_data = [[
                Paragraph("Szacowana cena od", price_label_style),
            ], [
                Paragraph(f"{lead.estimated_price_min:,.0f} PLN".replace(',', ' '), price_style),
            ]]

            price_table = Table(price_box_data, colWidths=[16*cm])
            price_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f0fff4')),
                ('BOX', (0, 0), (-1, -1), 2, success_color),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            content.append(price_table)

            content.append(Spacer(1, 10))
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                fontName=polish_font,
                fontSize=9,
                textColor=HexColor('#718096'),
                alignment=TA_CENTER
            )
            content.append(Paragraph(
                "* Ostateczna cena zalezy od wybranego materialu i szczegolów wykonania",
                disclaimer_style
            ))

        # Footer
        content.append(Spacer(1, 30))
        content.append(HRFlowable(
            width="100%",
            thickness=1,
            color=border_color,
            spaceAfter=15
        ))
        content.append(Paragraph(
            "Wycena wygenerowana automatycznie. Skontaktujemy sie z Panstwem w celu potwierdzenia szczególów.",
            footer_style
        ))
        content.append(Paragraph(
            f"Data wygenerowania: {lead.created_at.strftime('%d.%m.%Y %H:%M')}",
            footer_style
        ))

        # Build PDF
        doc.build(content)

        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
