import csv
from datetime import date
from decimal import Decimal
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone

from .forms import (
    ClienteForm, ProveedorForm, ProductoForm, TrabajadorForm,
    ComprobanteVentaForm, DetalleVentaFormSet,
    ComprobanteCompraForm, DetalleCompraFormSet,
)
from .models import (
    Empresa, EmpresaUsuario, Cliente, Proveedor, Producto, MovimientoStock,
    ComprobanteVenta, ComprobanteCompra, Pago, Trabajador, Planilla, DetallePlanilla,
)
from .planilla import calcular_detalle

IGV_FACTOR = Decimal('1.18')


# ---------------------------------------------------------------- helpers

def _empresa_activa(request):
    user = request.user
    if not user.is_authenticated:
        return None
    membresias = user.membresias.select_related('empresa').all()
    if not membresias:
        return None
    eid = request.session.get('empresa_id')
    if eid:
        m = membresias.filter(empresa_id=eid).first()
        if m:
            return m.empresa
    return membresias[0].empresa


def empresa_requerida(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if _empresa_activa(request) is None:
            messages.warning(request, 'Primero crea tu empresa para continuar.')
            return redirect('core:crear_empresa')
        return view_func(request, *args, **kwargs)
    return wrapper


def _ctx(request, **extra):
    ctx = {'empresa': _empresa_activa(request)}
    ctx.update(extra)
    return ctx


def _totales_detalles(detalles):
    """Dada una lista de detalles (cantidad, precio_unitario, afecto), calcula base/igv/total."""
    subtotal = Decimal('0')
    igv = Decimal('0')
    total = Decimal('0')
    for d in detalles:
        importe = (d['cantidad'] * d['precio_unitario']).quantize(Decimal('0.01'))
        afecto = d.get('afecto', True)
        if afecto:
            base = (importe / IGV_FACTOR).quantize(Decimal('0.01'))
            igv_linea = importe - base
        else:
            base = importe
            igv_linea = Decimal('0')
        subtotal += base
        igv += igv_linea
        total += importe
    return subtotal, igv, total


# ---------------------------------------------------------------- auth

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        nombre = request.POST.get('nombre', '').strip()
        razon_social = request.POST.get('razon_social', '').strip()
        ruc = request.POST.get('ruc', '').strip()

        error = None
        if not username or not password or not razon_social or not ruc:
            error = 'Completa todos los campos obligatorios.'
        elif len(ruc) != 11 or not ruc.isdigit():
            error = 'El RUC debe tener 11 dígitos.'
        elif User.objects.filter(username=username).exists():
            error = 'Ese usuario ya está registrado.'
        elif Empresa.objects.filter(ruc=ruc).exists():
            error = 'Ese RUC ya está registrado.'

        if error:
            messages.error(request, error)
        else:
            with transaction.atomic():
                user = User.objects.create_user(username=username, password=password, first_name=nombre)
                empresa = Empresa.objects.create(razon_social=razon_social, ruc=ruc)
                EmpresaUsuario.objects.create(empresa=empresa, usuario=user, rol='propietario')
            login(request, user)
            return redirect('core:dashboard')
    return render(request, 'core/register.html')


@login_required
def crear_empresa(request):
    if _empresa_activa(request) is not None:
        return redirect('core:dashboard')
    if request.method == 'POST':
        razon_social = request.POST.get('razon_social', '').strip()
        ruc = request.POST.get('ruc', '').strip()
        error = None
        if not razon_social or not ruc:
            error = 'Completa la razón social y el RUC.'
        elif len(ruc) != 11 or not ruc.isdigit():
            error = 'El RUC debe tener 11 dígitos.'
        elif Empresa.objects.filter(ruc=ruc).exists():
            error = 'Ese RUC ya está registrado.'
        if error:
            messages.error(request, error)
        else:
            with transaction.atomic():
                empresa = Empresa.objects.create(razon_social=razon_social, ruc=ruc)
                EmpresaUsuario.objects.create(empresa=empresa, usuario=request.user, rol='propietario')
            messages.success(request, 'Empresa creada.')
            return redirect('core:dashboard')
    return render(request, 'core/crear_empresa.html')


# ---------------------------------------------------------------- dashboard

@empresa_requerida
def dashboard(request):
    empresa = _empresa_activa(request)
    mes = date.today().replace(day=1)
    ventas = ComprobanteVenta.objects.filter(empresa=empresa, estado='emitido')
    compras = ComprobanteCompra.objects.filter(empresa=empresa, estado='registrado')

    return render(request, 'core/dashboard.html', _ctx(request,
        n_clientes=Cliente.objects.filter(empresa=empresa).count(),
        n_proveedores=Proveedor.objects.filter(empresa=empresa).count(),
        n_productos=Producto.objects.filter(empresa=empresa, activo=True).count(),
        stock_bajo=Producto.objects.filter(
            empresa=empresa, activo=True, stock_minimo__gt=0, stock__lte=F('stock_minimo')
        ).count(),
        ventas_mes=sum(v.total for v in ventas.filter(fecha__gte=mes)),
        compras_mes=sum(c.total for c in compras.filter(fecha__gte=mes)),
        por_cobrar=sum(v.saldo_pendiente for v in ventas if v.saldo_pendiente > 0),
        por_pagar=sum(c.saldo_pendiente for c in compras if c.saldo_pendiente > 0),
        ultimas_ventas=ventas[:5],
    ))


# ---------------------------------------------------------------- clientes

@empresa_requerida
def lista_clientes(request):
    empresa = _empresa_activa(request)
    q = request.GET.get('q', '').strip()
    clientes = Cliente.objects.filter(empresa=empresa)
    if q:
        clientes = clientes.filter(nombre__icontains=q) | clientes.filter(nro_doc__icontains=q)
    return render(request, 'core/clientes_list.html', _ctx(request, clientes=clientes, q=q))


@empresa_requerida
def cliente_crear(request):
    empresa = _empresa_activa(request)
    form = ClienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.empresa = empresa
        obj.save()
        messages.success(request, 'Cliente creado.')
        return redirect('core:lista_clientes')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Nuevo cliente'))


@empresa_requerida
def cliente_editar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Cliente, pk=pk, empresa=empresa)
    form = ClienteForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cliente actualizado.')
        return redirect('core:lista_clientes')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Editar cliente'))


@empresa_requerida
def cliente_eliminar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Cliente, pk=pk, empresa=empresa)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Cliente eliminado.')
        return redirect('core:lista_clientes')
    return render(request, 'core/confirmar.html', _ctx(request, objeto=obj, titulo='Eliminar cliente'))


# ---------------------------------------------------------------- proveedores

@empresa_requerida
def lista_proveedores(request):
    empresa = _empresa_activa(request)
    q = request.GET.get('q', '').strip()
    proveedores = Proveedor.objects.filter(empresa=empresa)
    if q:
        proveedores = proveedores.filter(nombre__icontains=q) | proveedores.filter(nro_doc__icontains=q)
    return render(request, 'core/proveedores_list.html', _ctx(request, proveedores=proveedores, q=q))


@empresa_requerida
def proveedor_crear(request):
    empresa = _empresa_activa(request)
    form = ProveedorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.empresa = empresa
        obj.save()
        messages.success(request, 'Proveedor creado.')
        return redirect('core:lista_proveedores')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Nuevo proveedor'))


@empresa_requerida
def proveedor_editar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Proveedor, pk=pk, empresa=empresa)
    form = ProveedorForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Proveedor actualizado.')
        return redirect('core:lista_proveedores')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Editar proveedor'))


@empresa_requerida
def proveedor_eliminar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Proveedor, pk=pk, empresa=empresa)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Proveedor eliminado.')
        return redirect('core:lista_proveedores')
    return render(request, 'core/confirmar.html', _ctx(request, objeto=obj, titulo='Eliminar proveedor'))


# ---------------------------------------------------------------- productos / inventario

@empresa_requerida
def lista_productos(request):
    empresa = _empresa_activa(request)
    q = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(empresa=empresa)
    if q:
        productos = productos.filter(descripcion__icontains=q) | productos.filter(codigo__icontains=q)
    return render(request, 'core/productos_list.html', _ctx(request, productos=productos, q=q))


@empresa_requerida
def producto_crear(request):
    empresa = _empresa_activa(request)
    form = ProductoForm(request.POST or None)
    form.fields['categoria'].queryset = empresa.categorias.all()
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.empresa = empresa
        obj.save()
        if obj.stock:
            MovimientoStock.objects.create(empresa=empresa, producto=obj, tipo='entrada',
                                           cantidad=obj.stock, descripcion='Stock inicial')
        messages.success(request, 'Producto creado.')
        return redirect('core:lista_productos')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Nuevo producto'))


@empresa_requerida
def producto_editar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Producto, pk=pk, empresa=empresa)
    form = ProductoForm(request.POST or None, instance=obj)
    form.fields['categoria'].queryset = empresa.categorias.all()
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('core:lista_productos')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Editar producto'))


@empresa_requerida
def producto_eliminar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Producto, pk=pk, empresa=empresa)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('core:lista_productos')
    return render(request, 'core/confirmar.html', _ctx(request, objeto=obj, titulo='Eliminar producto'))


# ---------------------------------------------------------------- ventas

@empresa_requerida
def lista_ventas(request):
    empresa = _empresa_activa(request)
    q = request.GET.get('q', '').strip()
    ventas = ComprobanteVenta.objects.filter(empresa=empresa)
    if q:
        ventas = ventas.filter(numero__icontains=q) | ventas.filter(cliente__nombre__icontains=q)
    return render(request, 'core/ventas_list.html', _ctx(request, ventas=ventas, q=q))


@empresa_requerida
def venta_crear(request):
    empresa = _empresa_activa(request)
    form = ComprobanteVentaForm(request.POST or None)
    form.fields['cliente'].queryset = empresa.clientes.all()
    formset = DetalleVentaFormSet(request.POST or None, prefix='detalles')
    qs = empresa.productos.filter(activo=True)
    for f in formset.forms:
        f.fields['producto'].queryset = qs
    formset.empty_form.fields['producto'].queryset = qs

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                comp = form.save(commit=False)
                comp.empresa = empresa
                comp.save()
                subtotal = Decimal('0'); igv = Decimal('0'); total = Decimal('0')
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('descripcion'):
                        d = f.save(commit=False)
                        d.comprobante = comp
                        d.importe = (d.cantidad * d.precio_unitario).quantize(Decimal('0.01'))
                        afecto = d.producto.afecto_igv if d.producto else True
                        if afecto:
                            base = (d.importe / IGV_FACTOR).quantize(Decimal('0.01'))
                            igv_linea = d.importe - base
                        else:
                            base = d.importe
                            igv_linea = Decimal('0')
                        subtotal += base; igv += igv_linea; total += d.importe
                        d.save()
                        if d.producto:
                            d.producto.stock -= d.cantidad
                            d.producto.save()
                            MovimientoStock.objects.create(
                                empresa=empresa, producto=d.producto, tipo='venta',
                                cantidad=-d.cantidad, referencia=f'{comp.serie}-{comp.numero}')
                comp.subtotal = subtotal; comp.igv = igv; comp.total = total
                comp.save()
            messages.success(request, f'Venta {comp.serie}-{comp.numero} registrada.')
            return redirect('core:venta_detalle', pk=comp.pk)
    return render(request, 'core/venta_form.html', _ctx(request, form=form, formset=formset, titulo='Nueva venta'))


@empresa_requerida
def venta_detalle(request, pk):
    empresa = _empresa_activa(request)
    comp = get_object_or_404(ComprobanteVenta, pk=pk, empresa=empresa)
    return render(request, 'core/venta_detalle.html', _ctx(request, comp=comp))


@empresa_requerida
def venta_anular(request, pk):
    empresa = _empresa_activa(request)
    comp = get_object_or_404(ComprobanteVenta, pk=pk, empresa=empresa)
    if request.method == 'POST' and comp.estado != 'anulado':
        with transaction.atomic():
            for d in comp.detalles.all():
                if d.producto:
                    d.producto.stock += d.cantidad
                    d.producto.save()
                    MovimientoStock.objects.create(
                        empresa=empresa, producto=d.producto, tipo='ajuste', cantidad=d.cantidad,
                        descripcion=f'Anulación {comp.serie}-{comp.numero}')
            comp.estado = 'anulado'
            comp.save()
        messages.success(request, 'Venta anulada (stock restaurado).')
        return redirect('core:lista_ventas')
    return render(request, 'core/confirmar.html', _ctx(request, objeto=comp, titulo='Anular venta'))


# ---------------------------------------------------------------- compras

@empresa_requerida
def lista_compras(request):
    empresa = _empresa_activa(request)
    q = request.GET.get('q', '').strip()
    compras = ComprobanteCompra.objects.filter(empresa=empresa)
    if q:
        compras = compras.filter(numero__icontains=q) | compras.filter(proveedor__nombre__icontains=q)
    return render(request, 'core/compras_list.html', _ctx(request, compras=compras, q=q))


@empresa_requerida
def compra_crear(request):
    empresa = _empresa_activa(request)
    form = ComprobanteCompraForm(request.POST or None)
    form.fields['proveedor'].queryset = empresa.proveedores.all()
    formset = DetalleCompraFormSet(request.POST or None, prefix='detalles')
    qs = empresa.productos.all()
    for f in formset.forms:
        f.fields['producto'].queryset = qs
    formset.empty_form.fields['producto'].queryset = qs

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                comp = form.save(commit=False)
                comp.empresa = empresa
                comp.save()
                subtotal = Decimal('0'); igv = Decimal('0'); total = Decimal('0')
                for f in formset:
                    if f.cleaned_data and not f.cleaned_data.get('DELETE') and f.cleaned_data.get('descripcion'):
                        d = f.save(commit=False)
                        d.comprobante = comp
                        d.importe = (d.cantidad * d.precio_unitario).quantize(Decimal('0.01'))
                        afecto = d.producto.afecto_igv if d.producto else True
                        if afecto:
                            base = (d.importe / IGV_FACTOR).quantize(Decimal('0.01'))
                            igv_linea = d.importe - base
                        else:
                            base = d.importe
                            igv_linea = Decimal('0')
                        subtotal += base; igv += igv_linea; total += d.importe
                        d.save()
                        if d.producto:
                            d.producto.stock += d.cantidad
                            d.producto.save()
                            MovimientoStock.objects.create(
                                empresa=empresa, producto=d.producto, tipo='compra',
                                cantidad=d.cantidad, referencia=f'{comp.serie}-{comp.numero}')
                comp.subtotal = subtotal; comp.igv = igv; comp.total = total
                comp.save()
            messages.success(request, f'Compra {comp.serie}-{comp.numero} registrada.')
            return redirect('core:compra_detalle', pk=comp.pk)
    return render(request, 'core/compra_form.html', _ctx(request, form=form, formset=formset, titulo='Nueva compra'))


@empresa_requerida
def compra_detalle(request, pk):
    empresa = _empresa_activa(request)
    comp = get_object_or_404(ComprobanteCompra, pk=pk, empresa=empresa)
    return render(request, 'core/compra_detalle.html', _ctx(request, comp=comp))


@empresa_requerida
def compra_anular(request, pk):
    empresa = _empresa_activa(request)
    comp = get_object_or_404(ComprobanteCompra, pk=pk, empresa=empresa)
    if request.method == 'POST' and comp.estado != 'anulado':
        with transaction.atomic():
            for d in comp.detalles.all():
                if d.producto:
                    d.producto.stock -= d.cantidad
                    d.producto.save()
                    MovimientoStock.objects.create(
                        empresa=empresa, producto=d.producto, tipo='ajuste', cantidad=-d.cantidad,
                        descripcion=f'Anulación {comp.serie}-{comp.numero}')
            comp.estado = 'anulado'
            comp.save()
        messages.success(request, 'Compra anulada (stock revertido).')
        return redirect('core:lista_compras')
    return render(request, 'core/confirmar.html', _ctx(request, objeto=comp, titulo='Anular compra'))


# ---------------------------------------------------------------- cuentas por cobrar / pagar

@empresa_requerida
def lista_por_cobrar(request):
    empresa = _empresa_activa(request)
    ventas = [v for v in ComprobanteVenta.objects.filter(empresa=empresa, estado='emitido')
              .select_related('cliente') if v.saldo_pendiente > 0]
    total = sum(v.saldo_pendiente for v in ventas)
    return render(request, 'core/por_cobrar.html', _ctx(request, items=ventas, total=total))


@empresa_requerida
def lista_por_pagar(request):
    empresa = _empresa_activa(request)
    compras = [c for c in ComprobanteCompra.objects.filter(empresa=empresa, estado='registrado')
               .select_related('proveedor') if c.saldo_pendiente > 0]
    total = sum(c.saldo_pendiente for c in compras)
    return render(request, 'core/por_pagar.html', _ctx(request, items=compras, total=total))


@empresa_requerida
def registrar_pago(request, tipo, pk):
    empresa = _empresa_activa(request)
    if tipo == 'cobro':
        comp = get_object_or_404(ComprobanteVenta, pk=pk, empresa=empresa)
        tipo_pago = 'cobro'
    else:
        comp = get_object_or_404(ComprobanteCompra, pk=pk, empresa=empresa)
        tipo_pago = 'pago'

    saldo = comp.saldo_pendiente
    if request.method == 'POST':
        try:
            monto = Decimal(request.POST.get('monto', '0'))
        except Exception:
            monto = Decimal('0')
        if monto <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
        elif monto > saldo:
            messages.error(request, f'El monto supera el saldo pendiente ({saldo}).')
        else:
            pago = Pago(empresa=empresa, tipo=tipo_pago, fecha=request.POST.get('fecha') or date.today(),
                        monto=monto, metodo=request.POST.get('metodo', 'efectivo'),
                        referencia=request.POST.get('referencia', ''))
            if tipo == 'cobro':
                pago.venta = comp
            else:
                pago.compra = comp
            pago.save()
            messages.success(request, 'Pago registrado.')
            return redirect('core:lista_por_cobrar' if tipo == 'cobro' else 'core:lista_por_pagar')
    return render(request, 'core/registrar_pago.html', _ctx(request, comp=comp, tipo=tipo, saldo=saldo))


# ---------------------------------------------------------------- reportes

@empresa_requerida
def reporte(request):
    empresa = _empresa_activa(request)
    mes = date.today().replace(day=1)
    ventas = ComprobanteVenta.objects.filter(empresa=empresa, estado='emitido')
    compras = ComprobanteCompra.objects.filter(empresa=empresa, estado='registrado')
    v_mes = ventas.filter(fecha__gte=mes)
    c_mes = compras.filter(fecha__gte=mes)
    return render(request, 'core/reporte.html', _ctx(request,
        ventas_mes=sum(v.total for v in v_mes),
        compras_mes=sum(c.total for c in c_mes),
        igv_ventas_mes=sum(v.igv for v in v_mes),
        igv_compras_mes=sum(c.igv for c in c_mes),
    ))


@empresa_requerida
def exportar_ventas_csv(request):
    empresa = _empresa_activa(request)
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="ventas.csv"'
    w = csv.writer(resp)
    w.writerow(['Fecha', 'Tipo', 'Serie', 'Número', 'Cliente', 'RUC/DNI', 'Subtotal', 'IGV', 'Total', 'Estado'])
    for v in ComprobanteVenta.objects.filter(empresa=empresa).select_related('cliente'):
        w.writerow([v.fecha, v.get_tipo_display(), v.serie, v.numero, v.cliente.nombre,
                    v.cliente.nro_doc, v.subtotal, v.igv, v.total, v.get_estado_display()])
    return resp


@empresa_requerida
def exportar_compras_csv(request):
    empresa = _empresa_activa(request)
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="compras.csv"'
    w = csv.writer(resp)
    w.writerow(['Fecha', 'Tipo', 'Serie', 'Número', 'Proveedor', 'RUC/DNI', 'Subtotal', 'IGV', 'Total', 'Estado'])
    for c in ComprobanteCompra.objects.filter(empresa=empresa).select_related('proveedor'):
        w.writerow([c.fecha, c.get_tipo_display(), c.serie, c.numero, c.proveedor.nombre,
                    c.proveedor.nro_doc, c.subtotal, c.igv, c.total, c.get_estado_display()])
    return resp


# ---------------------------------------------------------------- planilla

@empresa_requerida
def lista_trabajadores(request):
    empresa = _empresa_activa(request)
    q = request.GET.get('q', '').strip()
    trabajadores = Trabajador.objects.filter(empresa=empresa)
    if q:
        trabajadores = (trabajadores.filter(nombres__icontains=q)
                        | trabajadores.filter(apellidos__icontains=q)
                        | trabajadores.filter(dni__icontains=q))
    return render(request, 'core/trabajadores_list.html', _ctx(request, trabajadores=trabajadores, q=q))


@empresa_requerida
def trabajador_crear(request):
    empresa = _empresa_activa(request)
    form = TrabajadorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.empresa = empresa
        obj.save()
        messages.success(request, 'Trabajador creado.')
        return redirect('core:lista_trabajadores')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Nuevo trabajador'))


@empresa_requerida
def trabajador_editar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Trabajador, pk=pk, empresa=empresa)
    form = TrabajadorForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Trabajador actualizado.')
        return redirect('core:lista_trabajadores')
    return render(request, 'core/form.html', _ctx(request, form=form, titulo='Editar trabajador'))


@empresa_requerida
def trabajador_eliminar(request, pk):
    empresa = _empresa_activa(request)
    obj = get_object_or_404(Trabajador, pk=pk, empresa=empresa)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Trabajador eliminado.')
        return redirect('core:lista_trabajadores')
    return render(request, 'core/confirmar.html', _ctx(request, objeto=obj, titulo='Eliminar trabajador'))


@empresa_requerida
def lista_planillas(request):
    empresa = _empresa_activa(request)
    planillas = Planilla.objects.filter(empresa=empresa)
    return render(request, 'core/planillas_list.html', _ctx(request, planillas=planillas))


@empresa_requerida
def planilla_crear(request):
    empresa = _empresa_activa(request)
    hoy = date.today()
    if request.method == 'POST':
        try:
            mes = int(request.POST.get('mes', hoy.month))
            anio = int(request.POST.get('anio', hoy.year))
        except (TypeError, ValueError):
            mes, anio = hoy.month, hoy.year
        if not (1 <= mes <= 12):
            messages.error(request, 'Mes inválido.')
        elif Planilla.objects.filter(empresa=empresa, mes=mes, anio=anio).exists():
            messages.error(request, 'Ya existe una planilla para ese mes.')
        else:
            with transaction.atomic():
                planilla = Planilla.objects.create(empresa=empresa, mes=mes, anio=anio)
                t_ing = t_desc = t_neto = t_essalud = Decimal('0')
                for t in Trabajador.objects.filter(empresa=empresa, activo=True):
                    c = calcular_detalle(t)
                    DetallePlanilla.objects.create(planilla=planilla, trabajador=t, **c)
                    t_ing += c['total_ingresos']
                    t_desc += c['descuento_pension'] + c['renta_5ta']
                    t_neto += c['neto_pagar']
                    t_essalud += c['aporte_essalud']
                planilla.total_ingresos = t_ing
                planilla.total_descuentos = t_desc
                planilla.total_neto = t_neto
                planilla.total_essalud = t_essalud
                planilla.save()
            messages.success(request, f'Planilla {mes:02d}/{anio} generada.')
            return redirect('core:planilla_detalle', pk=planilla.pk)
    return render(request, 'core/planilla_form.html', _ctx(request, hoy=hoy))


@empresa_requerida
def planilla_detalle(request, pk):
    empresa = _empresa_activa(request)
    planilla = get_object_or_404(Planilla, pk=pk, empresa=empresa)
    return render(request, 'core/planilla_detalle.html', _ctx(request, planilla=planilla))


@empresa_requerida
def planilla_cerrar(request, pk):
    empresa = _empresa_activa(request)
    planilla = get_object_or_404(Planilla, pk=pk, empresa=empresa)
    if request.method == 'POST':
        planilla.estado = 'cerrada'
        planilla.save()
        messages.success(request, 'Planilla cerrada.')
        return redirect('core:planilla_detalle', pk=planilla.pk)
    return render(request, 'core/confirmar.html', _ctx(request, objeto=planilla, titulo='Cerrar planilla'))


@empresa_requerida
def planilla_export_csv(request, pk):
    empresa = _empresa_activa(request)
    planilla = get_object_or_404(Planilla, pk=pk, empresa=empresa)
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="planilla_{planilla.mes:02d}_{planilla.anio}.csv"'
    w = csv.writer(resp)
    w.writerow(['DNI', 'Trabajador', 'Cargo', 'Régimen pensión', 'Días', 'Sueldo',
                'Asig. familiar', 'Total ingresos', 'Descuento pensión', 'Renta 5ta',
                'Neto a pagar', 'EsSalud (empleador)'])
    for d in planilla.detalles.select_related('trabajador'):
        w.writerow([d.trabajador.dni, d.trabajador.nombre_completo, d.trabajador.cargo,
                    d.trabajador.get_regimen_pension_display(), d.dias, d.sueldo,
                    d.asignacion_familiar, d.total_ingresos, d.descuento_pension,
                    d.renta_5ta, d.neto_pagar, d.aporte_essalud])
    return resp
