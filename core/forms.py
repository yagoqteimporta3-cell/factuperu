from django import forms
from django.forms import inlineformset_factory
from .models import (
    Cliente, Proveedor, Producto, ComprobanteVenta, DetalleVenta,
    ComprobanteCompra, DetalleCompra, Trabajador,
)


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['tipo_doc', 'nro_doc', 'nombre', 'direccion', 'telefono', 'email']


class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['tipo_doc', 'nro_doc', 'nombre', 'direccion', 'telefono', 'email']


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'descripcion', 'categoria', 'unidad', 'precio_compra',
                  'precio_venta', 'stock', 'stock_minimo', 'afecto_igv', 'activo']


class ComprobanteVentaForm(forms.ModelForm):
    class Meta:
        model = ComprobanteVenta
        fields = ['tipo', 'serie', 'numero', 'fecha', 'fecha_vencimiento', 'cliente',
                  'forma_pago', 'moneda', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }


class ComprobanteCompraForm(forms.ModelForm):
    class Meta:
        model = ComprobanteCompra
        fields = ['tipo', 'serie', 'numero', 'fecha', 'fecha_vencimiento', 'proveedor',
                  'moneda', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }


DetalleVentaFormSet = inlineformset_factory(
    ComprobanteVenta, DetalleVenta,
    fields=['producto', 'descripcion', 'cantidad', 'precio_unitario'],
    extra=1, can_delete=True,
)

DetalleCompraFormSet = inlineformset_factory(
    ComprobanteCompra, DetalleCompra,
    fields=['producto', 'descripcion', 'cantidad', 'precio_unitario'],
    extra=1, can_delete=True,
)


class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombres', 'apellidos', 'dni', 'fecha_nacimiento', 'cargo',
                  'fecha_ingreso', 'sueldo_base', 'regimen_pension', 'afp_entidad',
                  'regimen_salud', 'asignacion_familiar', 'tipo_contrato', 'activo']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
        }
