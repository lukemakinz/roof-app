"""
AI processor service for extracting roof dimensions from images using OpenAI Vision.
"""
import os
import base64
import json
from pathlib import Path
from django.conf import settings

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def encode_image_to_base64(image_path):
    """Encode image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.standard_b64encode(image_file.read()).decode("utf-8")


def get_image_media_type(image_path):
    """Get MIME type based on file extension."""
    ext = Path(image_path).suffix.lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return media_types.get(ext, 'image/jpeg')


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
        # Try to extract number from string like "40" or "40°"
        import re
        match = re.search(r'(\d+)', str(kat))
        if match:
            kat = int(match.group(1))
            validation_warnings.append(f"Kąt nachylenia wyekstrahowany z tekstu: {kat}°")
        else:
            kat = 0

    # If angle is 0 or unrealistic, add warning but DON'T set default
    # Let the user know it needs verification
    if kat == 0:
        validation_warnings.append("UWAGA: Kąt nachylenia nie został znaleziony na rysunku - wymaga ręcznej weryfikacji")
        # Set a placeholder that will be obvious to the user
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
            # Probably millimeters, divide by 1000
            corrected_dlugosc = dlugosc_cm / 1000
            validation_warnings.append(f"Wymiar {dlugosc_cm} interpretowany jako mm → {corrected_dlugosc}m")
        else:
            # Centimeters, divide by 100
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
    
    # Dimensions should be between 5m and 35m for typical houses
    if dlugosc_m < 5 or dlugosc_m > 35:
        validation_warnings.append(f"UWAGA: Długość {dlugosc_m}m poza typowym zakresem (5-35m) - wymaga weryfikacji")
    
    if szerokosc_m < 5 or szerokosc_m > 35:
        validation_warnings.append(f"UWAGA: Szerokość {szerokosc_m}m poza typowym zakresem (5-35m) - wymaga weryfikacji")
    
    # RULE 3: Recalculate surface area based on corrected dimensions
    if dlugosc_m > 0 and szerokosc_m > 0:
        pomiary = data.get('pomiary', {})
        # Simple rectangle approximation for plan area
        plan_area = dlugosc_m * szerokosc_m
        kat_dla_obliczen = data.get('kat_nachylenia', 0)
        # Use 30° as calculation fallback only if angle is 0 (not found)
        if kat_dla_obliczen == 0:
            kat_dla_obliczen = 30  # Conservative estimate for calculations only
            validation_warnings.append("Do obliczeń powierzchni użyto domyślnego kąta 30° (brak danych)")
        import math
        real_area = plan_area / math.cos(math.radians(kat_dla_obliczen)) if kat_dla_obliczen > 0 else plan_area
        
        old_area = pomiary.get('powierzchnia_dachu_m2', 0)
        if abs(real_area - old_area) > 20:  # More than 20m² difference
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

    # Get key values
    elementy = data.get('elementy_dodatkowe', {})
    pomiary = data.get('pomiary', {})
    rynny = data.get('system_odwodnienia', {})
    pewnosc = data.get('pewnosc_oszacowania', 'srednia')
    elementy_niepewne = data.get('elementy_niepewne', [])

    kominy = elementy.get('kominy_szt', 0)
    kominki = elementy.get('kominki_wentylacyjne_szt', 0)
    okna = elementy.get('okna_dachowe_szt', 0)
    wylazy = elementy.get('wylazy_dachowe_szt', 0)
    powierzchnia = pomiary.get('powierzchnia_dachu_m2', 0)
    okapy = pomiary.get('dlugosc_okapow_m', 0)

    # RULE 0: Sanity check - total elements should not exceed chimneys + reasonable extras
    # AI often hallucinates by counting the same element multiple times as different things
    total_elements = kominy + kominki + okna + wylazy
    if total_elements > kominy + 2:
        # Suspicious - AI might be double-counting
        validation_warnings.append(
            f"UWAGA: Suma elementów ({total_elements}) wydaje się za wysoka - możliwe podwójne liczenie"
        )

    # RULE 1: Low/medium confidence = be very conservative with rare elements
    if pewnosc in ['niska', 'srednia']:
        # Skylights are rare - zero them unless high confidence
        if okna > 0:
            validation_warnings.append(f"Przy pewności '{pewnosc}' wyzerowano okna dachowe (było: {okna}) - wymagają oznaczenia 'OD'")
            elementy['okna_dachowe_szt'] = 0
        # Roof hatches are very rare
        if wylazy > 0:
            validation_warnings.append(f"Przy pewności '{pewnosc}' wyzerowano wyłazy dachowe (było: {wylazy}) - wymagają oznaczenia 'WD'")
            elementy['wylazy_dachowe_szt'] = 0
        # Ventilation caps are also rare
        if kominki > 0:
            validation_warnings.append(f"Przy pewności '{pewnosc}' wyzerowano kominki wentylacyjne (było: {kominki}) - wymagają widocznych kółek")
            elementy['kominki_wentylacyjne_szt'] = 0

    # RULE 2: Even with high confidence, apply strict limits
    # Max 4 chimneys for any house
    if kominy > 4:
        validation_warnings.append(f"Skorygowano liczbę kominów z {kominy} do 4 (maksimum dla typowego domu)")
        elementy['kominy_szt'] = 4

    # Max 2 skylights (rare on roof plans)
    if okna > 2:
        validation_warnings.append(f"Skorygowano liczbę okien dachowych z {okna} do 2 (rzadko więcej na rzucie)")
        elementy['okna_dachowe_szt'] = 2

    # Max 1 roof hatch (very rare)
    if wylazy > 1:
        validation_warnings.append(f"Skorygowano liczbę wyłazów z {wylazy} do 1 (rzadko więcej niż 1)")
        elementy['wylazy_dachowe_szt'] = 1

    # Max 2 ventilation caps
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
    if any('went' in e or 'komin' in e and 'went' in e for e in elementy_niepewne_lower):
        if elementy.get('kominki_wentylacyjne_szt', 0) > 0:
            validation_warnings.append("Wyzerowano kominki wentylacyjne - były na liście niepewnych elementów")
            elementy['kominki_wentylacyjne_szt'] = 0

    # RULE 4: Auto-fill gutter system if missing but eaves present
    if okapy > 0:
        if rynny.get('rury_spustowe_szt', 0) == 0:
            # ~1 downpipe per 10m of eave
            expected_rury = max(2, int(okapy / 10))
            rynny['rury_spustowe_szt'] = expected_rury
            validation_warnings.append(f"Auto-uzupełniono rury spustowe: {expected_rury} szt.")

    # Update data
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
    
    # Dwuspadowy prosty should NOT have valleys or junctions
    if typ == 'dwuspadowy' and (kosze > 0 or trojniki > 0):
        validation_warnings.append(
            f"Typ '{typ}' nie powinien mieć koszy ({kosze}m) ani trójników ({trojniki}szt) - prawdopodobnie wielospadowy"
        )
        if kosze > 0:
            data['typ_dachu'] = 'wielospadowy'
    
    # Jednospadowy/pulpitowy should NOT have ridges
    if typ in ['jednospadowy', 'pulpitowy']:
        if kalenice > 0:
            pomiary['dlugosc_kalenic_m'] = 0
            validation_warnings.append(f"Wyzerowano kalenice dla dachu {typ}")
        if trojniki > 0:
            gasiory['trojniki_szt'] = 0
    
    # Płaski should have minimal pitch
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


def process_roof_image(image_path):
    """
    Process roof image using OpenAI Vision API to extract dimensions.
    
    Returns:
        dict with extracted data or None if processing failed
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key or not OPENAI_AVAILABLE:
        # Return mock data if no API key
        return create_mock_response()
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Encode image
        image_data = encode_image_to_base64(image_path)
        media_type = get_image_media_type(image_path)
        
        # Enhanced roof analysis prompt with anti-hallucination rules
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

### 1B. KĄT NACHYLENIA DACHU - SZUKAJ BARDZO DOKŁADNIE!

⚠️ PRIORYTET NAJWYŻSZY: Znajdź DOKŁADNY kąt nachylenia na rysunku! NIE ZGADUJ!

**JAK WYGLĄDA KĄT NA POLSKICH RYSUNKACH TECHNICZNYCH:**
Na polskich rysunkach kąt nachylenia jest oznaczony SPECYFICZNIE:
- MAŁY ŁUK (półkole) ze STRZAŁKĄ przy linii ukośnej dachu
- LICZBA (np. 40, 35, 25) jest napisana OBOK tego łuku
- Symbol ° (stopni) często jest POMINIĘTY!
- Może wyglądać jak: "40" z małym łukiem obok, lub ".40" lub "40."
- Strzałka wskazuje kierunek spadku dachu

**PRZYKŁAD:** Jeśli widzisz małą kreskę ukośną z łukiem i liczbą "40" obok - TO JEST KĄT 40°!

**Gdzie szukać (SPRAWDŹ KAŻDE MIEJSCE!):**
1. Przy LINII UKOŚNEJ reprezentującej połać dachu - szukaj małego łuku z liczbą!
2. W przekrojach A-A lub B-B
3. W widoku ELEWACJA (bok budynku)
4. Przy krawędzi dachu gdzie widać spadek
5. W legendzie/opisie rysunku

**ABSOLUTNIE KRYTYCZNE:**
- Szukaj LICZBY DWUCYFROWEJ (40, 35, 25, 45) obok małego łuku lub strzałki!
- Jeśli widzisz "40" przy łuku/strzałce → wpisz 40
- Jeśli widzisz "35" przy linii dachu → wpisz 35
- Symbol ° może nie być widoczny - liczy się sama LICZBA przy łuku!
- NIE ZGADUJ "typowych" wartości jak 30° czy 35°!
- Jeśli naprawdę NIE MA kąta na rysunku → wpisz 0

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
- Jeśli NIE widzisz oznaczenia "OD"/"okno"/"świetlik" → okna_dachowe_szt = 0
- DOMYŚLNIE: 0 (większość dachów nie ma okien dachowych na rzucie!)

**KOMINEK WENTYLACYJNY (kominki_wentylacyjne_szt):**
- JEDYNY sposób identyfikacji: MAŁE KÓŁKO (okrąg) o średnicy ~10-15cm
- Może mieć oznaczenie "KW", "W", "went.", "wentylacja"
- ⚠️ To NIE jest duży kwadrat - to małe kółko!
- ⚠️ Jeśli widzisz tylko kwadraty z X → to są KOMINY, nie kominki wentylacyjne
- Jeśli NIE widzisz małych kółek → kominki_wentylacyjne_szt = 0
- DOMYŚLNIE: 0 (kominki wentylacyjne są rzadkie!)

**WYŁAZ DACHOWY (wylazy_dachowe_szt):**
- JEDYNY sposób identyfikacji: mały kwadrat Z WYRAŹNYM OZNACZENIEM "wyłaz", "WD", "właz"
- ⚠️ Sam mały kwadrat bez oznaczenia to NIE JEST wyłaz!
- Jeśli NIE widzisz oznaczenia "wyłaz"/"WD" → wylazy_dachowe_szt = 0
- DOMYŚLNIE: 0 (wyłazy są bardzo rzadkie!)

### TABELA ROZRÓŻNIANIA ELEMENTÓW:
| Element widzę | Ma krzyż X? | Ma oznaczenie? | To jest: |
|---------------|-------------|----------------|----------|
| Duży kwadrat  | TAK         | -              | KOMIN    |
| Duży kwadrat  | NIE         | "OD"/"okno"    | OKNO DACHOWE |
| Duży kwadrat  | NIE         | brak           | IGNORUJ (nie wiadomo co) |
| Małe kółko    | -           | -              | KOMINEK WENTYLACYJNY |
| Mały kwadrat  | NIE         | "wyłaz"/"WD"   | WYŁAZ    |
| Mały kwadrat  | NIE         | brak           | IGNORUJ  |

⚠️ KRYTYCZNE ZASADY:
1. Policz TYLKO elementy które WYRAŹNIE widzisz i możesz zidentyfikować!
2. Kwadrat z X = ZAWSZE KOMIN (nigdy okno!)
3. Jeśli nie jesteś 100% pewien co to jest → wpisz 0
4. NIE ZGADUJ! Lepiej wpisać 0 niż zmyślić element którego nie ma
5. Typowy dom ma 1-2 kominy, 0 okien dachowych, 0 kominków wentylacyjnych, 0 wyłazów

### 5. ELEMENTY GĄSIOROWE - LOGIKA:
- TRÓJNIK = punkt gdzie spotykają się 3+ kalenic
- GĄSIOR NAROŻNY = na krawędziach koszy (dolin)
- GĄSIOR POCZĄTKOWY = start kalenicy od strony okapu  
- GĄSIOR KOŃCOWY = koniec kalenicy przy szczycie
- Jednospadowy: trojniki=0, kalenicy=0

### 6. FORMAT ODPOWIEDZI (TYLKO JSON):

⚠️ KRYTYCZNE: Zwróć TYLKO wartości liczbowe! NIE używaj formuł, wyrażeń matematycznych ani kodu JavaScript!
❌ ŹLE: "powierzchnia_dachu_m2": 12.5 * 9.8 * 2 / Math.cos(kat * Math.PI / 180)
✅ DOBRZE: "powierzchnia_dachu_m2": 165.2

WSZYSTKIE wartości muszą być:
- Obliczone PRZED zwróceniem JSON
- Oparte na tym co WIDZISZ na rysunku (nie zgaduj!)
- Liczbami (nie stringami z opisami)

STRUKTURA JSON (zastąp opisy konkretnymi wartościami z rysunku):

{
    "typ_dachu": "JEDEN Z: jednospadowy|dwuspadowy|dwuspadowy_l|czterospadowy|kopertowy|wielospadowy|wielospadowy_l|mansardowy|naczolkowy|pulpitowy|plaski",
    "kat_nachylenia": "LICZBA: DOKŁADNY kąt odczytany z rysunku (np. jeśli widzisz 40° wpisz 40, jeśli 38° wpisz 38) - NIE ZGADUJ! Wpisz 0 tylko jeśli kąta nie ma na rysunku",
    "wymiary_surowe": {
        "dlugosc_cm": "LICZBA: surowa wartość odczytana z rysunku w cm",
        "szerokosc_cm": "LICZBA: surowa wartość odczytana z rysunku w cm"
    },
    "wymiary_budynku": {
        "dlugosc_m": "LICZBA: wymiary_surowe.dlugosc_cm podzielone przez 100",
        "szerokosc_m": "LICZBA: wymiary_surowe.szerokosc_cm podzielone przez 100"
    },
    "pomiary": {
        "powierzchnia_dachu_m2": "LICZBA: obliczona na podstawie wymiarów i kąta",
        "dlugosc_krawedzi_szczytowych_lewych_m": "LICZBA: zmierzona lub 0",
        "dlugosc_krawedzi_szczytowych_prawych_m": "LICZBA: zmierzona lub 0",
        "dlugosc_kalenic_m": "LICZBA: zmierzona lub 0 dla jednospadowego",
        "dlugosc_koszy_m": "LICZBA: zmierzona lub 0",
        "dlugosc_okapow_m": "LICZBA: suma wszystkich okapów"
    },
    "elementy_gasiorowe": {
        "trojniki_szt": "LICZBA: policzone punkty lub 0",
        "gasiory_narozne_szt": "LICZBA: policzone lub 0",
        "gasiory_poczatkowe_szt": "LICZBA: policzone lub 0",
        "gasiory_koncowe_szt": "LICZBA: policzone lub 0"
    },
    "elementy_dodatkowe": {
        "kominy_szt": "LICZBA: policzone widoczne kwadraty z X lub 0",
        "kominki_wentylacyjne_szt": "LICZBA: policzone małe kółka lub 0",
        "okna_dachowe_szt": "LICZBA: policzone lub 0",
        "wylazy_dachowe_szt": "LICZBA: policzone lub 0"
    },
    "system_odwodnienia": {
        "narozniki_rynien_szt": "LICZBA: policzone lub 0",
        "rury_spustowe_szt": "LICZBA: policzone lub 0",
        "zaslepki_rynien_szt": "LICZBA: policzone lub 0"
    },
    "pewnosc_oszacowania": "JEDEN Z: niska|srednia|wysoka",
    "elementy_niepewne": ["lista stringów z elementami których nie jesteś pewien"],
    "uwagi": "WYMAGANE: Napisz tutaj 'Kąt na rysunku: XX°' (dokładna wartość którą widzisz) + inne obserwacje"
}

⚠️ ZASTĄP WSZYSTKIE OPISY KONKRETNYMI WARTOŚCIAMI! Zwróć WYŁĄCZNIE poprawny JSON. Żadnych formuł, żadnego kodu, żadnego markdown."""
        
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
            import logging
            logging.info(f"Angle extraction response: '{angle_text}'")

            # Extract number from response
            import re
            angle_match = re.search(r'(\d+)', angle_text)
            extracted_angle = int(angle_match.group(1)) if angle_match else 0
            logging.info(f"Extracted angle: {extracted_angle}")

        except Exception as e:
            import logging
            logging.error(f"Angle extraction failed: {e}")
            extracted_angle = 0

        # STEP 2: Main analysis with the extracted angle hint
        system_message = f"""Jesteś precyzyjnym ekspertem od analizy rysunków technicznych dachów.

WAŻNE: Wstępna analiza wykryła kąt nachylenia: {extracted_angle}°
Użyj tej wartości dla kat_nachylenia, chyba że WYRAŹNIE widzisz inną wartość na rysunku.

Jeśli wstępna analiza dała 0, oznacza to że kąt nie został znaleziony - wtedy też wpisz 0."""

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

        # Log raw response for debugging
        import logging
        logging.info(f"AI raw response (first 1000 chars): {response_text[:1000] if response_text else 'EMPTY'}")

        # Handle empty response
        if not response_text:
            return {
                'success': False,
                'error': 'AI returned empty response'
            }

        # Clean up response - remove markdown code blocks if present
        response_text = response_text.strip()

        # Remove markdown code blocks
        if response_text.startswith('```'):
            # Remove opening ```json or ```
            first_newline = response_text.find('\n')
            if first_newline != -1:
                response_text = response_text[first_newline + 1:]

        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        # Try to extract JSON if there's extra text
        if not response_text.startswith('{'):
            # Find the first { character
            json_start = response_text.find('{')
            if json_start != -1:
                response_text = response_text[json_start:]

        if not response_text.endswith('}'):
            # Find the last } character
            json_end = response_text.rfind('}')
            if json_end != -1:
                response_text = response_text[:json_end + 1]

        result = json.loads(response_text)
        
        # Apply post-processing validation (dimensions first!)
        result = validate_dimensions(result)
        result = validate_ai_response(result)
        result = validate_roof_type_consistency(result)
        
        return {
            'success': True,
            'data': result
        }
        
    except json.JSONDecodeError as e:
        # Log the problematic response for debugging
        import logging
        logging.error(f"Failed to parse AI response. Error: {str(e)}")
        logging.error(f"Raw response (first 500 chars): {response_text[:500] if 'response_text' in dir() else 'N/A'}")
        
        # Try to fix common JSON issues
        try:
            if 'response_text' in dir():
                # Remove any comments (// style)
                import re
                cleaned = re.sub(r'//.*$', '', response_text, flags=re.MULTILINE)
                # Remove trailing commas before } or ]
                cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
                result = json.loads(cleaned)
                
                result = validate_dimensions(result)
                result = validate_ai_response(result)
                result = validate_roof_type_consistency(result)
                
                return {
                    'success': True,
                    'data': result
                }
        except:
            pass
        
        return {
            'success': False,
            'error': f'Failed to parse AI response: {str(e)}. Check server logs for details.'
        }
    except Exception as e:
        import logging
        logging.error(f"AI processing error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def create_mock_response():
    """Create mock response for development/testing without API key."""
    mock_data = {
        'typ_dachu': 'wielospadowy',
        'kat_nachylenia': 25,
        'wymiary_surowe': {
            'dlugosc_cm': 1308,
            'szerokosc_cm': 1031
        },
        'wymiary_budynku': {
            'dlugosc_m': 13.08,
            'szerokosc_m': 10.31
        },
        'pomiary': {
            'powierzchnia_dachu_m2': 420,
            'dlugosc_krawedzi_szczytowych_lewych_m': 8.5,
            'dlugosc_krawedzi_szczytowych_prawych_m': 8.5,
            'dlugosc_kalenic_m': 12.0,
            'dlugosc_koszy_m': 6.0,
            'dlugosc_okapow_m': 45.0
        },
        'elementy_gasiorowe': {
            'trojniki_szt': 2,
            'gasiory_narozne_szt': 4,
            'gasiory_poczatkowe_szt': 4,
            'gasiory_koncowe_szt': 4
        },
        'elementy_dodatkowe': {
            'kominy_szt': 2,
            'kominki_wentylacyjne_szt': 0,  # 0 - nie zgadujemy
            'okna_dachowe_szt': 1,
            'wylazy_dachowe_szt': 0
        },
        'system_odwodnienia': {
            'narozniki_rynien_szt': 4,
            'rury_spustowe_szt': 4,
            'zaslepki_rynien_szt': 4
        },
        'pewnosc_oszacowania': 'srednia',
        'elementy_niepewne': [],
        'uwagi': 'Mock data - brak klucza API'
    }
    
    # Apply validation to mock data too
    mock_data = validate_ai_response(mock_data)
    mock_data = validate_roof_type_consistency(mock_data)
    
    return {
        'success': True,
        'data': mock_data
    }
