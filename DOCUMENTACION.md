# FactuPerú — Estado del Proyecto

**Software de gestión contable para empresas peruanas** (facturación, inventario, cobros/pagos y planilla), pensado para venderlo como servicio, similar a Siigo Nube o NubeCont.

Fecha: noviembre 2026
Estado: **Fase 1 y Fase 2 terminadas y funcionando.**

---

## 1. Qué se hizo (terminado y funcionando)

### Fase 1 — Núcleo contable
- **Cuentas y empresas**: registro, inicio de sesión, una cuenta puede manejar varias empresas.
- **Clientes y proveedores**: alta, edición, eliminación y búsqueda (RUC/DNI, teléfono, correo).
- **Inventario**: productos con código, precio de compra/venta, stock y alerta de stock mínimo.
- **Ventas y compras**: facturas/boletas con varias líneas; el IGV (18%) y el total se calculan solos; el stock se descuenta o aumenta automáticamente; se pueden anular (restaurando el stock).
- **Cuentas por cobrar / por pagar**: saldos pendientes, registro de cobros y pagos a cuotas.
- **Reportes**: resumen del mes y exportación a Excel/CSV (para el contador).

### Fase 2 — Planilla de trabajadores
- **Trabajadores**: datos personales, DNI, cargo, sueldo, régimen ONP o AFP, asignación familiar.
- **Planilla mensual**: genera automáticamente la planilla del mes con:
  - Sueldo + asignación familiar.
  - Descuento de pensión: ONP 13% o AFP (~12.5%).
  - Renta de 5ta categoría (escala progresiva con deducción de 7 UIT).
  - EsSalud 9% (a cargo del empleador).
  - Neto a pagar por trabajador.
- **Boletas** por trabajador, totales, exportación a CSV y cierre de planilla.

Todo está **verificado con pruebas automáticas** (cálculos de IGV, stock y planilla confirmados).

---

## 2. Qué tenemos aquí mismo (cómo está montado)

| Elemento | Detalle |
|---|---|
| **Tecnología** | Python + Django 5.1 + base de datos SQLite (local) |
| **Dónde corre** | En tu PC, en `http://127.0.0.1:8000` |
| **Código** | `C:\Users\PC\Proyectos\factuperu` |
| **Acceso de prueba** | Usuario `admin` / contraseña `admin12345` (empresa demo "Empresa Demo SAC") |
| **Estado** | App web funcional en modo local (desarrollo) |

> Hoy corre solo en tu computadora. Para que tus clientes la usen desde internet hay que subirla a un servidor en la nube (ver sección 4).

---

## 3. Qué se va a hacer (pendiente)

### Fase 3 — Facturación electrónica SUNAT
- Emitir facturas y boletas electrónicas reales integrando un **OSE/PSE** (Nubefact, el más usado).
- Requiere que cada cliente tenga RUC activo, clave SOL y certificado digital.

### Fase 4 — Planilla completa
- PLAME oficial (formato SUNAT) y T-Registro.
- Días trabajados, horas extra, gratificaciones, CTS y vacaciones.

### Otras mejoras
- Generar las facturas en PDF.
- Edición de comprobantes ya emitidos.
- Respaldos automáticos.
- Roles de usuario (por ejemplo, acceso para el contador de cada cliente).
- Página de venta (landing) y sistema de cobro de suscripciones.
- Pasar la base de datos a PostgreSQL (obligatorio en producción).

---

## 4. Qué se necesita (para venderlo en serio)

### Técnico (costos bajos al inicio)
| Necesidad | Costo aproximado |
|---|---|
| Servidor en la nube (Render) | **$0** para empezar, ~$7–20/mes en plan pago |
| Base de datos PostgreSQL (Neon/Supabase) | **$0** en plan gratis |
| Dominio propio (.pe) | ~$10–40/año |

### Legal / SUNAT (lo importante)
- **Facturación electrónica**: cada cliente necesita RUC activo, usuario/clave SOL y un **certificado digital**, además de contratar un OSE (Nubefact). Esto tiene un costo mensual que normalmente lo paga el cliente.
- **Valores legales** (RMV, UIT, tasas de AFP/ONP) cambian cada año y deben actualizarse en el sistema.
- **Validación de un contador**: el cálculo de planilla (renta de 5ta, PLAME) debe ser revisado por un contador antes de usarse en producción real.

### Humano / operación (el punto crítico)
- **Alguien debe mantener el software**: actualizarlo cuando SUNAT cambie reglas, corregir errores y atender soporte a clientes. Sin esto, el sistema queda obsoleto en meses y los clientes se van.
- Esto requiere una persona que sepa programar + reglas contables peruanas, o pagarle a alguien.

---

## Resumen rápido
- ✅ **Hecho y funcionando**: facturación, inventario, clientes/proveedores, cobros/pagos, reportes y planilla.
- ⏳ **Pendiente**: facturación electrónica SUNAT, PLAME oficial y subirlo a la nube.
- 💡 **Para vender**: hace falta servidor + base de datos en la nube (~$0 para arrancar), el OSE/certificado para SUNAT, y una persona que mantenga el sistema.
