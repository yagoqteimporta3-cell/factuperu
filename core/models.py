from django.db import models
from django.contrib.auth.models import User


class Empresa(models.Model):
    REGIMENES = [
        ('general', 'Régimen General'),
        ('mype', 'Régimen MYPE Tributario'),
        ('especial', 'Régimen Especial'),
        ('rer', 'Nuevo RUS'),
    ]
    razon_social = models.CharField('Razón social', max_length=200)
    ruc = models.CharField('RUC', max_length=11, unique=True)
    nombre_comercial = models.CharField(max_length=200, blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    regimen = models.CharField(max_length=20, choices=REGIMENES, default='mype')
    moneda = models.CharField(max_length=3, default='PEN')
    activa = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['razon_social']

    def __str__(self):
        return f'{self.razon_social} ({self.ruc})'


class EmpresaUsuario(models.Model):
    ROLES = [
        ('propietario', 'Propietario'),
        ('contador', 'Contador'),
        ('empleado', 'Empleado'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='miembros')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membresias')
    rol = models.CharField(max_length=20, choices=ROLES, default='propietario')

    class Meta:
        unique_together = ('empresa', 'usuario')

    def __str__(self):
        return f'{self.usuario} -> {self.empresa}'


class Cliente(models.Model):
    TIPO_DOC = [
        ('dni', 'DNI'),
        ('ruc', 'RUC'),
        ('ce', 'Carné de Extranjería'),
        ('pasaporte', 'Pasaporte'),
        ('otro', 'Otro'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='clientes')
    tipo_doc = models.CharField('Tipo de documento', max_length=10, choices=TIPO_DOC, default='dni')
    nro_doc = models.CharField('N° de documento', max_length=20)
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        unique_together = ('empresa', 'tipo_doc', 'nro_doc')

    def __str__(self):
        return f'{self.nombre} ({self.nro_doc})'


class Proveedor(models.Model):
    TIPO_DOC = [
        ('dni', 'DNI'),
        ('ruc', 'RUC'),
        ('ce', 'Carné de Extranjería'),
        ('pasaporte', 'Pasaporte'),
        ('otro', 'Otro'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='proveedores')
    tipo_doc = models.CharField('Tipo de documento', max_length=10, choices=TIPO_DOC, default='ruc')
    nro_doc = models.CharField('N° de documento', max_length=20)
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nombre']
        unique_together = ('empresa', 'tipo_doc', 'nro_doc')

    def __str__(self):
        return f'{self.nombre} ({self.nro_doc})'


class Categoria(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='categorias')
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ['nombre']
        unique_together = ('empresa', 'nombre')

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    UNIDADES = [
        ('und', 'Unidad'),
        ('caja', 'Caja'),
        ('doc', 'Docena'),
        ('kg', 'Kilogramo'),
        ('lt', 'Litro'),
        ('mt', 'Metro'),
        ('servicio', 'Servicio'),
        ('otro', 'Otro'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='productos')
    codigo = models.CharField('Código', max_length=40, blank=True)
    descripcion = models.CharField('Descripción', max_length=250)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    unidad = models.CharField(max_length=10, choices=UNIDADES, default='und')
    precio_compra = models.DecimalField('Precio de compra', max_digits=12, decimal_places=2, default=0)
    precio_venta = models.DecimalField('Precio de venta', max_digits=12, decimal_places=2, default=0)
    stock = models.DecimalField('Stock', max_digits=12, decimal_places=2, default=0)
    stock_minimo = models.DecimalField('Stock mínimo', max_digits=12, decimal_places=2, default=0)
    afecto_igv = models.BooleanField('Afecto a IGV', default=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['descripcion']

    def __str__(self):
        return f'{self.codigo} - {self.descripcion}' if self.codigo else self.descripcion


class MovimientoStock(models.Model):
    TIPOS = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('compra', 'Compra'),
        ('venta', 'Venta'),
        ('ajuste', 'Ajuste'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='movimientos_stock')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=100, blank=True)
    descripcion = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.tipo}: {self.producto} x {self.cantidad}'


class ComprobanteVenta(models.Model):
    TIPOS = [
        ('factura', 'Factura (01)'),
        ('boleta', 'Boleta (03)'),
        ('nota_credito', 'Nota de crédito (07)'),
        ('nota_debito', 'Nota de débito (08)'),
    ]
    ESTADOS = [
        ('emitido', 'Emitido'),
        ('anulado', 'Anulado'),
    ]
    FORMAS_PAGO = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='ventas')
    tipo = models.CharField('Tipo', max_length=15, choices=TIPOS, default='factura')
    serie = models.CharField('Serie', max_length=4, default='F001')
    numero = models.CharField('Número', max_length=10)
    fecha = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas')
    forma_pago = models.CharField(max_length=10, choices=FORMAS_PAGO, default='contado')
    moneda = models.CharField(max_length=3, default='PEN')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='emitido')
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-creado']
        unique_together = ('empresa', 'tipo', 'serie', 'numero')

    def __str__(self):
        return f'{self.get_tipo_display()} {self.serie}-{self.numero}'

    @property
    def saldo_pendiente(self):
        pagado = sum(p.monto for p in self.cobros.all())
        return self.total - pagado


class DetalleVenta(models.Model):
    comprobante = models.ForeignKey(ComprobanteVenta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=250)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    importe = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.descripcion} x {self.cantidad}'


class ComprobanteCompra(models.Model):
    TIPOS = [
        ('factura', 'Factura (01)'),
        ('boleta', 'Boleta (03)'),
        ('nota_credito', 'Nota de crédito (07)'),
        ('nota_debito', 'Nota de débito (08)'),
    ]
    ESTADOS = [
        ('registrado', 'Registrado'),
        ('anulado', 'Anulado'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='compras')
    tipo = models.CharField('Tipo', max_length=15, choices=TIPOS, default='factura')
    serie = models.CharField('Serie', max_length=4, blank=True)
    numero = models.CharField('Número', max_length=20)
    fecha = models.DateField()
    fecha_vencimiento = models.DateField(null=True, blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    moneda = models.CharField(max_length=3, default='PEN')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='registrado')
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-creado']

    def __str__(self):
        return f'{self.get_tipo_display()} {self.serie}-{self.numero}'

    @property
    def saldo_pendiente(self):
        pagado = sum(p.monto for p in self.pagos.all())
        return self.total - pagado


class DetalleCompra(models.Model):
    comprobante = models.ForeignKey(ComprobanteCompra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=250)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    importe = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f'{self.descripcion} x {self.cantidad}'


class Pago(models.Model):
    TIPOS = [
        ('cobro', 'Cobro a cliente'),
        ('pago', 'Pago a proveedor'),
    ]
    METODOS = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta', 'Tarjeta'),
        ('cheque', 'Cheque'),
        ('otro', 'Otro'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pagos')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    venta = models.ForeignKey(ComprobanteVenta, on_delete=models.CASCADE, null=True, blank=True, related_name='cobros')
    compra = models.ForeignKey(ComprobanteCompra, on_delete=models.CASCADE, null=True, blank=True, related_name='pagos')
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=15, choices=METODOS, default='efectivo')
    referencia = models.CharField(max_length=100, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.get_tipo_display()}: {self.monto}'


class Trabajador(models.Model):
    REG_PENSION = [
        ('onp', 'ONP (Sistema Nacional de Pensiones - 13%)'),
        ('afp', 'AFP (Sistema Privado de Pensiones)'),
    ]
    TIPO_CONTRATO = [
        ('indefinido', 'Indefinido'),
        ('plazo_fijo', 'Plazo fijo'),
        ('tiempo_parcial', 'Tiempo parcial'),
        ('practicas', 'Prácticas'),
    ]
    REG_SALUD = [
        ('essalud', 'EsSalud'),
        ('eps', 'EPS'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='trabajadores')
    nombres = models.CharField('Nombres', max_length=120)
    apellidos = models.CharField('Apellidos', max_length=120)
    dni = models.CharField('DNI', max_length=8)
    fecha_nacimiento = models.DateField('Fecha de nacimiento', null=True, blank=True)
    cargo = models.CharField('Cargo', max_length=120, blank=True)
    fecha_ingreso = models.DateField('Fecha de ingreso', null=True, blank=True)
    sueldo_base = models.DecimalField('Remuneración mensual (S/)', max_digits=12, decimal_places=2)
    regimen_pension = models.CharField('Régimen de pensión', max_length=3, choices=REG_PENSION, default='onp')
    afp_entidad = models.CharField('AFP (si aplica)', max_length=40, blank=True)
    regimen_salud = models.CharField('Régimen de salud', max_length=10, choices=REG_SALUD, default='essalud')
    asignacion_familiar = models.BooleanField('Recibe asignación familiar', default=False)
    tipo_contrato = models.CharField('Tipo de contrato', max_length=20, choices=TIPO_CONTRATO, default='indefinido')
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['apellidos', 'nombres']
        unique_together = ('empresa', 'dni')

    def __str__(self):
        return f'{self.apellidos}, {self.nombres}'

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'


class Planilla(models.Model):
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('cerrada', 'Cerrada'),
    ]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='planillas')
    mes = models.IntegerField('Mes')
    anio = models.IntegerField('Año')
    estado = models.CharField(max_length=10, choices=ESTADOS, default='borrador')
    total_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_descuentos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_essalud = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-anio', '-mes']
        unique_together = ('empresa', 'mes', 'anio')

    def __str__(self):
        return f'Planilla {self.mes:02d}/{self.anio}'


class DetallePlanilla(models.Model):
    planilla = models.ForeignKey(Planilla, on_delete=models.CASCADE, related_name='detalles')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='detalles_planilla')
    dias = models.IntegerField(default=30)
    sueldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    asignacion_familiar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    otros_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento_pension = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    renta_5ta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    neto_pagar = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    aporte_essalud = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.trabajador} - {self.planilla}'
