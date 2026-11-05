from django.contrib import admin
from .models import (
    Empresa, EmpresaUsuario, Cliente, Proveedor, Categoria, Producto,
    MovimientoStock, ComprobanteVenta, DetalleVenta, ComprobanteCompra,
    DetalleCompra, Pago, Trabajador, Planilla, DetallePlanilla,
)


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1


class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('razon_social', 'ruc', 'regimen', 'telefono', 'activa')
    search_fields = ('razon_social', 'ruc')
    list_filter = ('regimen', 'activa')


@admin.register(EmpresaUsuario)
class EmpresaUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'rol')
    list_filter = ('rol',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nro_doc', 'tipo_doc', 'telefono', 'empresa')
    search_fields = ('nombre', 'nro_doc')
    list_filter = ('tipo_doc', 'empresa')


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nro_doc', 'tipo_doc', 'telefono', 'empresa')
    search_fields = ('nombre', 'nro_doc')
    list_filter = ('tipo_doc', 'empresa')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'unidad', 'precio_venta', 'stock', 'empresa')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('categoria', 'empresa', 'afecto_igv')


@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'empresa')
    list_filter = ('tipo', 'empresa')


@admin.register(ComprobanteVenta)
class ComprobanteVentaAdmin(admin.ModelAdmin):
    list_display = ('serie', 'numero', 'cliente', 'fecha', 'total', 'estado', 'empresa')
    list_filter = ('tipo', 'estado', 'empresa')
    search_fields = ('serie', 'numero', 'cliente__nombre')
    inlines = [DetalleVentaInline]


@admin.register(ComprobanteCompra)
class ComprobanteCompraAdmin(admin.ModelAdmin):
    list_display = ('serie', 'numero', 'proveedor', 'fecha', 'total', 'estado', 'empresa')
    list_filter = ('tipo', 'estado', 'empresa')
    search_fields = ('serie', 'numero', 'proveedor__nombre')
    inlines = [DetalleCompraInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'fecha', 'monto', 'metodo', 'empresa')
    list_filter = ('tipo', 'metodo', 'empresa')


@admin.register(Trabajador)
class TrabajadorAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombre_completo', 'cargo', 'sueldo_base', 'regimen_pension', 'activo', 'empresa')
    search_fields = ('nombres', 'apellidos', 'dni')
    list_filter = ('regimen_pension', 'activo', 'empresa')


class DetallePlanillaInline(admin.TabularInline):
    model = DetallePlanilla
    extra = 0
    readonly_fields = ('trabajador', 'dias', 'sueldo', 'total_ingresos', 'descuento_pension', 'renta_5ta', 'neto_pagar')


@admin.register(Planilla)
class PlanillaAdmin(admin.ModelAdmin):
    list_display = ('mes', 'anio', 'estado', 'total_ingresos', 'total_neto', 'empresa')
    list_filter = ('estado', 'anio', 'empresa')
    inlines = [DetallePlanillaInline]
