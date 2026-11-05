import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from decimal import Decimal
from core.planilla import calcular_detalle
from core.models import Trabajador, Planilla, DetallePlanilla, Empresa, EmpresaUsuario, User

ok = lambda b: 'OK' if b else 'FAIL'

# --- Prueba directa de cálculo ---
class T:
    def __init__(self, sueldo, reg, asig=False):
        self.sueldo_base = Decimal(str(sueldo))
        self.regimen_pension = reg
        self.asignacion_familiar = asig

# Caso 1: ONP, sueldo 1500, sin asignación (renta 5ta = 0)
c1 = calcular_detalle(T(1500, 'onp'))
print('1 ONP 1500 -> pension=%.2f (195) renta=%.2f (0) neto=%.2f (1305) essalud=%.2f (135)' % (
    c1['descuento_pension'], c1['renta_5ta'], c1['neto_pagar'], c1['aporte_essalud']))
print('   ', ok(c1['descuento_pension'] == 195 and c1['renta_5ta'] == 0 and c1['neto_pagar'] == 1305 and c1['aporte_essalud'] == 135))

# Caso 2: ONP, sueldo 5000 (renta 5ta > 0)
c2 = calcular_detalle(T(5000, 'onp'))
print('2 ONP 5000 -> pension=%.2f (650) renta=%.2f (141) neto=%.2f (4209)' % (
    c2['descuento_pension'], c2['renta_5ta'], c2['neto_pagar']))
print('   ', ok(c2['descuento_pension'] == 650 and c2['renta_5ta'] == 141 and c2['neto_pagar'] == 4209))

# Caso 3: AFP, sueldo 1500, con asignación familiar
c3 = calcular_detalle(T(1500, 'afp', asig=True))
print('3 AFP 1500+asig -> ingresos=%.2f (1613) pension=%.2f (201.63) neto=%.2f' % (
    c3['total_ingresos'], c3['descuento_pension'], c3['neto_pagar']))
print('   ', ok(c3['total_ingresos'] == 1613 and c3['descuento_pension'] == 201.63))

# --- Flujo completo vía test client ---
c = Client()
c.login(username='admin', password='admin12345')

# Crear 2 trabajadores
r = c.post('/trabajadores/nuevo/', {
    'nombres': 'Juan', 'apellidos': 'Pérez', 'dni': '12345678', 'fecha_nacimiento': '1990-01-01',
    'cargo': 'Vendedor', 'fecha_ingreso': '2024-01-01', 'sueldo_base': '1500',
    'regimen_pension': 'onp', 'afp_entidad': '', 'regimen_salud': 'essalud',
    'asignacion_familiar': 'on', 'tipo_contrato': 'indefinido', 'activo': 'on',
})
r2 = c.post('/trabajadores/nuevo/', {
    'nombres': 'María', 'apellidos': 'Gómez', 'dni': '87654321', 'fecha_nacimiento': '1995-05-05',
    'cargo': 'Administradora', 'fecha_ingreso': '2024-03-01', 'sueldo_base': '5000',
    'regimen_pension': 'onp', 'afp_entidad': '', 'regimen_salud': 'essalud',
    'asignacion_familiar': '', 'tipo_contrato': 'indefinido', 'activo': 'on',
})
n_trab = Trabajador.objects.count()
print('4 trabajadores ->', r.status_code, r2.status_code, ok(n_trab == 2), '| total:', n_trab)

# Generar planilla noviembre 2026
r = c.post('/planilla/nueva/', {'mes': '11', 'anio': '2026'})
planilla = Planilla.objects.filter(mes=11, anio=2026).first()
print('5 planilla ->', r.status_code, ok(planilla is not None))
if planilla:
    print('   detalles:', planilla.detalles.count(), '(esp 2)')
    print('   total_ingresos=%.2f (esp 1613+5000=6613) total_neto=%.2f' % (planilla.total_ingresos, planilla.total_neto))
    print('   ', ok(planilla.detalles.count() == 2 and planilla.total_ingresos == 6613))

# Exportar CSV
r = c.get(f'/planilla/{planilla.pk}/exportar/')
print('6 export CSV ->', r.status_code, ok(r.status_code == 200 and 'Juan' in r.content.decode()))

# Cerrar planilla
r = c.post(f'/planilla/{planilla.pk}/cerrar/')
planilla.refresh_from_db()
print('7 cerrar ->', r.status_code, ok(planilla.estado == 'cerrada'))
