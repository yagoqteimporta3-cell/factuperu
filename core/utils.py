from decimal import Decimal

IGV_RATE = Decimal('0.18')


def calc_igv(subtotal, rate=IGV_RATE):
    """Dado el subtotal (base), devuelve (igv, total)."""
    subtotal = Decimal(str(subtotal))
    igv = (subtotal * rate).quantize(Decimal('0.01'))
    total = subtotal + igv
    return igv, total


def money(v):
    """Formatea un número como moneda peruana (solo número, sin símbolo)."""
    return f'{float(v or 0):,.2f}'
