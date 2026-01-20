"""
Calculation service for roof materials.
"""
import math
from decimal import Decimal


def calculate_roof_materials(quote, material):
    """
    Calculate all materials needed for a roof based on quote dimensions and selected material.
    
    Returns a dict with materials breakdown and financial summary.
    """
    # Get dimensions
    length = Decimal(str(quote.dimensions.get('length', 0)))
    width = Decimal(str(quote.dimensions.get('width', 0)))
    pitch_angle = quote.pitch_angle or 35
    
    # Get material config with defaults
    config = material.config or {}
    waste_factor = material.waste_factor or Decimal('1.12')
    
    # Configuration values
    battens_spacing_cm = config.get('battens_spacing_cm', 32)
    screws_per_m2 = config.get('screws_per_m2', 7)
    membrane_price_m2 = Decimal(str(config.get('membrane_price_m2', 7)))
    battens_price_mb = Decimal(str(config.get('battens_price_mb', 4)))
    counter_battens_price_mb = Decimal(str(config.get('counter_battens_price_mb', 5)))
    screws_price_per_100 = Decimal(str(config.get('screws_price_per_100', 30)))
    ridge_tape_price_mb = Decimal(str(config.get('ridge_tape_price_mb', 15)))
    
    # 1. Calculate areas
    plan_area = length * width
    pitch_radians = math.radians(pitch_angle)
    cos_pitch = Decimal(str(math.cos(pitch_radians)))
    real_area = plan_area / cos_pitch if cos_pitch > 0 else plan_area
    
    # 2. Calculate material with waste factor
    material_needed = real_area * waste_factor
    
    # 3. Calculate additional materials
    # Rafter height for battens length
    roof_height = (width / 2) * Decimal(str(math.tan(pitch_radians)))
    rafter_length = Decimal(str(math.sqrt(float((width / 2) ** 2 + roof_height ** 2))))
    
    # Battens: horizontal strips
    battens_rows = int(rafter_length * 100 / battens_spacing_cm) + 1
    battens_meters = battens_rows * length * 2  # Both sides of roof
    
    # Counter-battens: vertical strips (assume ~10 per side)
    counter_battens_count = 10
    counter_battens_meters = counter_battens_count * rafter_length * 2
    
    # Membrane (similar to real area)
    membrane_area = real_area * Decimal('1.05')  # 5% overlap
    
    # Screws
    screws_quantity = int(material_needed * screws_per_m2)
    
    # Ridge tape (length of roof)
    ridge_length = length
    
    # 4. Calculate obstacle costs
    obstacles_area_reduction = Decimal('0')
    obstacles_extra_cost = Decimal('0')
    
    for obstacle in (quote.obstacles or []):
        qty = obstacle.get('quantity', 0)
        obs_type = obstacle.get('type', '')
        
        if obs_type == 'chimney':
            obstacles_area_reduction += Decimal('1') * qty
            obstacles_extra_cost += Decimal('50') * qty  # Chimney flashing
        elif obs_type == 'skylight':
            obstacles_area_reduction += Decimal('0.5') * qty
            obstacles_extra_cost += Decimal('80') * qty  # Skylight flashing
        elif obs_type == 'roof_hatch':
            obstacles_area_reduction += Decimal('0.8') * qty
            obstacles_extra_cost += Decimal('40') * qty  # Roof hatch flashing
        elif obs_type == 'vent_pipe':
            obstacles_area_reduction += Decimal('0.1') * qty
            obstacles_extra_cost += Decimal('35') * qty  # Vent pipe flashing
    
    # Adjust material needed for obstacles
    adjusted_material = material_needed - obstacles_area_reduction
    
    # 5. Calculate costs
    roofing_cost = adjusted_material * material.price_per_m2
    battens_cost = battens_meters * battens_price_mb
    counter_battens_cost = counter_battens_meters * counter_battens_price_mb
    membrane_cost = membrane_area * membrane_price_m2
    screws_cost = Decimal(screws_quantity) / 100 * screws_price_per_100
    ridge_tape_cost = ridge_length * ridge_tape_price_mb
    
    materials_net = (
        roofing_cost + battens_cost + counter_battens_cost + 
        membrane_cost + screws_cost + ridge_tape_cost + obstacles_extra_cost
    )
    
    # Labor cost based on margin
    margin_percent = quote.margin_percent or 35
    labor_cost = materials_net * Decimal(str(margin_percent)) / 100
    
    total_net = materials_net + labor_cost
    vat_rate = quote.vat_rate or 23
    vat = total_net * Decimal(str(vat_rate)) / 100
    total_gross = total_net + vat
    
    # Build result
    materials_breakdown = {
        'roofing': {
            'name': material.name,
            'quantity': round(float(adjusted_material), 1),
            'unit': 'm²',
            'unit_price': float(material.price_per_m2),
            'total': round(float(roofing_cost), 2)
        },
        'membrane': {
            'name': 'Membrana dachowa',
            'quantity': round(float(membrane_area), 1),
            'unit': 'm²',
            'unit_price': float(membrane_price_m2),
            'total': round(float(membrane_cost), 2)
        },
        'counter_battens': {
            'name': 'Kontrłaty',
            'quantity': round(float(counter_battens_meters), 1),
            'unit': 'mb',
            'unit_price': float(counter_battens_price_mb),
            'total': round(float(counter_battens_cost), 2)
        },
        'battens': {
            'name': 'Łaty',
            'quantity': round(float(battens_meters), 1),
            'unit': 'mb',
            'unit_price': float(battens_price_mb),
            'total': round(float(battens_cost), 2)
        },
        'screws': {
            'name': 'Wkręty montażowe',
            'quantity': screws_quantity,
            'unit': 'szt',
            'unit_price': round(float(screws_price_per_100 / 100), 3),
            'total': round(float(screws_cost), 2)
        },
        'ridge_tape': {
            'name': 'Taśma kalenicowa',
            'quantity': round(float(ridge_length), 1),
            'unit': 'mb',
            'unit_price': float(ridge_tape_price_mb),
            'total': round(float(ridge_tape_cost), 2)
        }
    }
    
    # Add obstacles if any
    if obstacles_extra_cost > 0:
        materials_breakdown['obstacles'] = {
            'name': 'Obróbki (kominy, okna, wyłazy, kominki went.)',
            'quantity': sum(o.get('quantity', 0) for o in (quote.obstacles or [])),
            'unit': 'szt',
            'unit_price': None,
            'total': round(float(obstacles_extra_cost), 2)
        }
    
    summary = {
        'materials_net': round(float(materials_net), 2),
        'labor_net': round(float(labor_cost), 2),
        'total_net': round(float(total_net), 2),
        'vat': round(float(vat), 2),
        'vat_rate': vat_rate,
        'total_gross': round(float(total_gross), 2)
    }
    
    return {
        'plan_area': round(float(plan_area), 2),
        'real_area': round(float(real_area), 2),
        'materials': materials_breakdown,
        'summary': summary
    }
