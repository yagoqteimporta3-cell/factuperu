"""Cálculos de planilla (Perú).

IMPORTANTE: los valores legales (RMV, UIT, tasas) cambian cada año.
Actualízalos aquí. El cálculo de renta de 5ta categoría es REFERENCIAL
(simplificado para sueldo fijo anualizado); un contador debe validarlo.
"""
from decimal import Decimal, ROUND_HALF_UP

# --- Parámetros legales (ACTUALIZAR cada año) ---
RMV = Decimal('1130.00')         # Remuneración Mínima Vital (S/ 1,130 desde mayo 2025)
UIT = Decimal('5550.00')         # Unidad Impositiva Tributaria 2026 (verificar vigente)
TASA_ONP = Decimal('0.13')       # Aporte obligatorio ONP (13%)
TASA_ESSALUD = Decimal('0.09')   # Aporte del EMPLEADOR a EsSalud (9%)
TASA_AFP = Decimal('0.125')      # AFP aprox. (fondo 10% + seguro 1.6% + comisión ~0.9%). Varía por AFP.
ASIGNACION_FAMILIAR = (RMV * Decimal('0.10')).quantize(Decimal('0.01'))  # 10% de la RMV
DIAS_MES = 30


def _q(v):
    return Decimal(str(v)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def impuesto_renta_anual(renta_neta_anual):
    """Impuesto anual de renta de trabajo (escala progresiva en UIT)."""
    r = Decimal(str(renta_neta_anual))
    if r <= 0:
        return Decimal('0')
    u = UIT
    if r <= 5 * u:
        imp = r * Decimal('0.08')
    elif r <= 20 * u:
        imp = 5 * u * Decimal('0.08') + (r - 5 * u) * Decimal('0.14')
    elif r <= 35 * u:
        imp = 5 * u * Decimal('0.08') + 15 * u * Decimal('0.14') + (r - 20 * u) * Decimal('0.17')
    elif r <= 45 * u:
        imp = 5 * u * Decimal('0.08') + 15 * u * Decimal('0.14') + 15 * u * Decimal('0.17') + (r - 35 * u) * Decimal('0.20')
    else:
        imp = (5 * u * Decimal('0.08') + 15 * u * Decimal('0.14') + 15 * u * Decimal('0.17')
               + 10 * u * Decimal('0.20') + (r - 45 * u) * Decimal('0.30'))
    return _q(imp)


def calcular_detalle(trabajador, dias=DIAS_MES, otros_ingresos=Decimal('0')):
    """Devuelve un dict con todos los conceptos calculados para un trabajador.

    Método simplificado (sueldo fijo, mes completo de 30 días). La renta de
    5ta categoría anualiza el sueldo mensual, deduce 7 UIT, aplica la escala
    progresiva y divide entre 12 (retención mensual referencial).
    """
    dias = int(dias or DIAS_MES)
    factor = Decimal(dias) / Decimal(DIAS_MES)
    sueldo = _q(trabajador.sueldo_base * factor)
    asig = _q((ASIGNACION_FAMILIAR if trabajador.asignacion_familiar else Decimal('0')) * factor)
    otros = _q(otros_ingresos)
    ingresos = _q(sueldo + asig + otros)

    if trabajador.regimen_pension == 'onp':
        desc_pension = _q(ingresos * TASA_ONP)
    else:
        desc_pension = _q(ingresos * TASA_AFP)

    renta_anual = ingresos * 12
    renta_neta_anual = renta_anual - (7 * UIT)
    impuesto_anual = impuesto_renta_anual(renta_neta_anual)
    renta_5ta = _q(impuesto_anual / 12)

    neto = _q(ingresos - desc_pension - renta_5ta)
    essalud = _q(ingresos * TASA_ESSALUD)  # lo paga el empleador, no se descuenta

    return {
        'dias': dias,
        'sueldo': sueldo,
        'asignacion_familiar': asig,
        'otros_ingresos': otros,
        'total_ingresos': ingresos,
        'descuento_pension': desc_pension,
        'renta_5ta': renta_5ta,
        'neto_pagar': neto,
        'aporte_essalud': essalud,
    }
