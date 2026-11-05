import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from core.models import Cliente, Proveedor, Producto, ComprobanteVenta, ComprobanteCompra, Pago, MovimientoStock

c = Client()
ok = lambda b: 'OK' if b else 'FAIL'

# 1. Registro
r = c.post('/register/', {'username': 'empresa1', 'password': 'pass12345', 'nombre': 'Carlos',
                          'razon_social': 'Mi Tienda EIRL', 'ruc': '20601234567'})
print('1 registro ->', r.status_code, ok(r.status_code == 302))

# 2. Cliente
r = c.post('/clientes/nuevo/', {'tipo_doc': 'ruc', 'nro_doc': '20555555555', 'nombre': 'Cliente Uno SAC',
                                'direccion': '', 'telefono': '', 'email': ''})
cliente = Cliente.objects.filter(nro_doc='20555555555').first()
print('2 cliente ->', r.status_code, ok(cliente is not None))

# 3. Proveedor
c.post('/proveedores/nuevo/', {'tipo_doc': 'ruc', 'nro_doc': '20444444444', 'nombre': 'Proveedor Uno SAC',
                               'direccion': '', 'telefono': '', 'email': ''})
proveedor = Proveedor.objects.filter(nro_doc='20444444444').first()
print('3 proveedor ->', ok(proveedor is not None))

# 4. Producto (stock inicial 100)
c.post('/productos/nuevo/', {'codigo': 'P001', 'descripcion': 'Cemento x bolsa', 'categoria': '',
                             'unidad': 'und', 'precio_compra': '20', 'precio_venta': '30',
                             'stock': '100', 'stock_minimo': '10', 'afecto_igv': 'on', 'activo': 'on'})
prod = Producto.objects.filter(codigo='P001').first()
print('4 producto ->', ok(prod is not None and prod.stock == 100), '| stock:', prod.stock)

# 5. Venta: 2 x S/30 (con IGV). Total esperado = 60, base = 50.85, igv = 9.15
venta_data = {
    'tipo': 'factura', 'serie': 'F001', 'numero': '0001', 'fecha': '2026-11-01',
    'fecha_vencimiento': '', 'cliente': str(cliente.pk), 'forma_pago': 'credito',
    'moneda': 'PEN', 'notas': '',
    'detalles-TOTAL_FORMS': '1', 'detalles-INITIAL_FORMS': '0',
    'detalles-MIN_NUM_FORMS': '0', 'detalles-MAX_NUM_FORMS': '1000',
    'detalles-0-producto': str(prod.pk), 'detalles-0-descripcion': 'Cemento x bolsa',
    'detalles-0-cantidad': '2', 'detalles-0-precio_unitario': '30',
    'detalles-0-id': '', 'detalles-0-DELETE': '',
}
r = c.post('/ventas/nuevo/', venta_data)
v = ComprobanteVenta.objects.filter(numero='0001').first()
prod.refresh_from_db()
print('5 venta ->', r.status_code, ok(v is not None))
if v:
    print('   total=%.2f (esp 60.00) subtotal=%.2f (esp 50.85) igv=%.2f (esp 9.15)' % (v.total, v.subtotal, v.igv))
    print('   detalles=', v.detalles.count(), '| stock despues=', prod.stock, '(esp 98)')

# 6. Compra: 10 x S/20 (con IGV), stock sube
compra_data = {
    'tipo': 'factura', 'serie': 'C001', 'numero': '100', 'fecha': '2026-11-01',
    'fecha_vencimiento': '', 'proveedor': str(proveedor.pk), 'moneda': 'PEN', 'notas': '',
    'detalles-TOTAL_FORMS': '1', 'detalles-INITIAL_FORMS': '0',
    'detalles-MIN_NUM_FORMS': '0', 'detalles-MAX_NUM_FORMS': '1000',
    'detalles-0-producto': str(prod.pk), 'detalles-0-descripcion': 'Cemento x bolsa',
    'detalles-0-cantidad': '10', 'detalles-0-precio_unitario': '20',
    'detalles-0-id': '', 'detalles-0-DELETE': '',
}
r = c.post('/compras/nuevo/', compra_data)
comp = ComprobanteCompra.objects.filter(numero='100').first()
prod.refresh_from_db()
print('6 compra ->', r.status_code, ok(comp is not None), '| stock despues=', prod.stock, '(esp 108)')

# 7. Por cobrar: la venta tiene saldo 60 (credito)
r = c.get('/por-cobrar/')
print('7 por-cobrar ->', r.status_code, ok('60.00' in r.content.decode() or '60,00' in r.content.decode()))

# 8. Registrar cobro de 30
r = c.post('/pago/cobro/%d/' % v.pk, {'monto': '30', 'fecha': '2026-11-01', 'metodo': 'efectivo', 'referencia': ''})
v.refresh_from_db()
print('8 cobro ->', r.status_code, ok(v.saldo_pendiente == 30), '| saldo=', v.saldo_pendiente)

# 9. Export CSV ventas
r = c.get('/reportes/exportar-ventas/')
print('9 csv ventas ->', r.status_code, ok(r.status_code == 200 and 'F001' in r.content.decode()))

# 10. Anular venta -> stock se restaura (+2): 108 + 2 = 110
r = c.post('/ventas/%d/anular/' % v.pk)
prod.refresh_from_db()
v.refresh_from_db()
print('10 anular ->', r.status_code, ok(v.estado == 'anulado' and prod.stock == 110), '| stock=', prod.stock, '| estado=', v.estado)

# 11. Movimientos de stock registrados
print('11 movimientos stock ->', MovimientoStock.objects.count())
