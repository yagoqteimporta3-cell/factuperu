# FactuPerú

Sistema web (SaaS) de gestión contable para empresas peruanas: ventas, compras,
inventario, cuentas por cobrar/pagar y reportes. Multiempresa, con IGV 18% automático.

## Módulos (Fase 1 — implementados)
- Registro / inicio de sesión (un usuario = una empresa, extensible a varias)
- Clientes y proveedores (CRUD + búsqueda)
- Productos / inventario con control de stock y stock mínimo
- Comprobantes de venta y compra con líneas, IGV y total automáticos
- Movimientos de stock automáticos (entrada, venta, compra, ajuste por anulación)
- Cuentas por cobrar / por pagar con registro de pagos (cobros/abonos)
- Reportes del mes + exportación CSV (ventas/compras)

## Pendiente (fases siguientes)
- Planilla de trabajadores (PLAME)
- Libros electrónicos PLE
- Facturación electrónica SUNAT vía OSE (Nubefact)

## Ejecutar en local (desarrollo)

```bash
cd ~/Proyectos/factuperu
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py runserver
```

Abrir http://127.0.0.1:8000

## Desplegar en producción (nube)

1. Crear una base PostgreSQL (Supabase/Neon/Render, plan gratis).
2. Configurar variables de entorno (archivo `.env`):
   - `SECRET_KEY` (clave secreta larga y aleatoria)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=tu-dominio.com`
   - `DATABASE_URL=postgres://usuario:clave@host:5432/nombre`
3. Recolectar estáticos: `./venv/Scripts/python.exe manage.py collectstatic --noinput`
4. Servir con gunicorn: `gunicorn config.wsgi` (Render/Railway lo hacen automático).

## Nota sobre SUNAT
Para emitir comprobantes electrónicos reales se requiere RUC activo, clave SOL,
certificado digital y un OSE/PSE (Nubefact, etc.). No es posible conectarse a SUNAT
directamente sin ser "Emisor Electrónico" autorizado.
