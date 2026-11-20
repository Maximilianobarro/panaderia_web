from decimal import Decimal

from django.db import models


class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    nombre_permiso = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'permiso'

    def __str__(self):
        return self.nombre_permiso


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    permisos = models.ManyToManyField(Permiso, through='RolPermiso', related_name='roles')
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'rol'

    def __str__(self):
        return self.nombre_rol


class RolPermiso(models.Model):
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column='rol_id_rol')
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column='permiso_id_permiso')

    class Meta:
        db_table = 'rol_permiso'
        unique_together = (('rol', 'permiso'),)


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'categoria'

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    email = models.CharField(max_length=100, blank=True, null=True)
    calle = models.CharField(max_length=80, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    fecha_alta = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    dni = models.IntegerField(unique=True)
    nombre_usuario = models.CharField(max_length=50, unique=True)
    contrasena_hash = models.CharField(max_length=255)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    activo = models.BooleanField(default=True)
    debe_cambiar_clave = models.BooleanField(default=True)
    fecha_alta = models.DateField(blank=True, null=True, auto_now_add=True)
    fecha_ultima_modificacion = models.DateField(blank=True, null=True, auto_now=True)
    fecha_baja = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    rol = models.ForeignKey(Rol, on_delete=models.DO_NOTHING, db_column='rol_id_rol')

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return self.nombre_usuario


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.DO_NOTHING, db_column='categoria_idcategoria')

    class Meta:
        db_table = 'producto'

    def __str__(self):
        return self.nombre

    @property
    def activo(self):
        return (self.estado or '').lower() == 'activo'


class Venta(models.Model):
    id_venta = models.AutoField(primary_key=True)
    fecha_hora = models.DateTimeField()
    medio_pago = models.CharField(max_length=30, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario')
    cliente = models.ForeignKey(Cliente, on_delete=models.DO_NOTHING, db_column='cliente_id_cliente')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_anulacion = models.DateTimeField(blank=True, null=True)
    motivo_anulacion = models.CharField(max_length=200, blank=True, null=True)
    usuario_anulacion = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usuario_anulacion_id_usuario',
        related_name='ventas_anuladas',
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'venta'

    def __str__(self):
        return f"Venta #{self.id_venta}"

    @property
    def numero_comprobante(self):
        return f"0001-{self.id_venta:08d}"


class Encargo(models.Model):
    ESTADO_PENDIENTE = 'Pendiente'
    ESTADO_ENTREGADO = 'Entregado'
    ESTADO_CANCELADO = 'Cancelado'

    id_encargo = models.AutoField(primary_key=True)
    fecha_pedido = models.DateField(blank=True, null=True)
    fecha_entrega_prevista = models.DateField(blank=True, null=True)
    senia = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, blank=True, null=True)
    medio_pago = models.CharField(max_length=20, blank=True, null=True)
    observacion = models.CharField(max_length=200, blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario')
    cliente = models.ForeignKey(Cliente, on_delete=models.DO_NOTHING, db_column='cliente_id_cliente')
    fecha_entrega_real = models.DateTimeField(blank=True, null=True)
    fecha_anulacion = models.DateTimeField(blank=True, null=True)
    motivo_anulacion = models.CharField(max_length=200, blank=True, null=True)
    usuario_anulacion = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usuario_anulacion_id_usuario',
        related_name='encargos_anulados',
        blank=True,
        null=True,
    )
    fecha_hora_registro = models.DateTimeField(blank=True, null=True)
    fecha_pago_saldo = models.DateTimeField(blank=True, null=True)
    medio_pago_saldo = models.CharField(max_length=30, blank=True, null=True)
    usuario_pago_saldo = models.ForeignKey(
        Usuario,
        on_delete=models.DO_NOTHING,
        db_column='usuario_pago_saldo_id_usuario',
        related_name='saldos_cobrados',
        blank=True,
        null=True,
    )

    class Meta:
        db_table = 'encargo'

    def __str__(self):
        return f"Encargo #{self.id_encargo}"

    @property
    def numero_comprobante(self):
        return f"0002-{self.id_encargo:08d}"

    @property
    def saldo(self):
        return self.total - (self.senia or 0)

    @property
    def saldo_pagado(self):
        return self.fecha_pago_saldo is not None or self.saldo <= 0


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, db_column='venta_id_venta')
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING, db_column='producto_id_producto')
    cantidad = models.IntegerField()
    precio_unitario_venta = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_venta'
        unique_together = (('venta', 'producto'),)

    def __str__(self):
        return f"Detalle venta {self.venta_id} - {self.producto_id}"


class DetalleEncargo(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING, db_column='producto_id_producto')
    encargo = models.ForeignKey(Encargo, on_delete=models.DO_NOTHING, db_column='encargo_id_encargo')
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    preparado = models.BooleanField(default=False)

    class Meta:
        db_table = 'detalle_encargo'
        unique_together = (('producto', 'encargo'),)

    def __str__(self):
        return f'{self.encargo.numero_comprobante} - {self.producto}'


class LogAuditoria(models.Model):
    id_log = models.AutoField(primary_key=True)
    fecha_hora = models.DateTimeField()
    usuario = models.ForeignKey(
        Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario',
        null=True, blank=True, related_name='logs_auditoria',
    )
    entidad = models.CharField(max_length=50)
    id_registro = models.IntegerField()
    accion = models.CharField(max_length=20)
    valores_anteriores = models.TextField(blank=True, null=True)
    valores_actuales = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'log_auditoria'

    def __str__(self):
        return f"{self.accion} {self.entidad} #{self.id_registro}"


class Insumo(models.Model):
    UNIDADES = ['kg', 'g', 'l', 'ml', 'unidades']
    MARGEN_CERCA = Decimal('1.25')

    id_insumo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=80)
    unidad = models.CharField(max_length=20)
    stock_actual = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    activo = models.BooleanField(default=True)
    productos = models.ManyToManyField(Producto, blank=True, related_name='insumos', db_table='insumo_producto')

    class Meta:
        db_table = 'insumo'

    def __str__(self):
        return self.nombre

    @property
    def nivel(self):
        if self.stock_actual <= 0:
            return 'sin'
        if self.stock_minimo > 0 and self.stock_actual <= self.stock_minimo:
            return 'bajo'
        if self.stock_minimo > 0 and self.stock_actual <= self.stock_minimo * self.MARGEN_CERCA:
            return 'cerca'
        return 'ok'


class MovimientoInsumo(models.Model):
    TIPO_ENTRADA = 'Entrada'
    TIPO_SALIDA = 'Salida'
    TIPOS = [TIPO_ENTRADA, TIPO_SALIDA]

    id_movimiento = models.AutoField(primary_key=True)
    insumo = models.ForeignKey(Insumo, on_delete=models.DO_NOTHING, db_column='insumo_id_insumo', related_name='movimientos')
    tipo = models.CharField(max_length=20)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    stock_resultante = models.DecimalField(max_digits=12, decimal_places=3)
    fecha_hora = models.DateTimeField()
    motivo = models.CharField(max_length=200)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario', related_name='movimientos_insumo')

    class Meta:
        db_table = 'movimiento_insumo'

    def __str__(self):
        return f'{self.tipo} {self.insumo} {self.cantidad}'


class NotaCredito(models.Model):
    id_nota_credito = models.AutoField(primary_key=True)
    encargo = models.OneToOneField(Encargo, on_delete=models.DO_NOTHING, db_column='encargo_id_encargo', related_name='nota_credito')
    fecha_hora = models.DateTimeField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    medio_devolucion = models.CharField(max_length=30)
    motivo = models.CharField(max_length=200)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario', related_name='notas_credito')

    class Meta:
        db_table = 'nota_credito'

    def __str__(self):
        return f'Nota de crédito {self.numero_comprobante}'

    @property
    def numero_comprobante(self):
        return f"0003-{self.id_nota_credito:08d}"


class CierreCaja(models.Model):
    ESTADO_ABIERTA = 'Abierta'
    ESTADO_CERRADA = 'Cerrada'

    id_cierre = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario', related_name='cierres_caja')
    estado = models.CharField(max_length=20, default='Cerrada')
    fondo_inicial = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    desde = models.DateTimeField()
    hasta = models.DateTimeField(blank=True, null=True)
    cantidad_ventas = models.IntegerField(default=0)
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_senias = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_saldos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_devoluciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    efectivo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transferencia = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tarjeta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_turno = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    efectivo_esperado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacion = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'cierre_caja'

    def __str__(self):
        return f'Cierre de caja {self.numero_comprobante} - {self.usuario}'

    @property
    def numero_comprobante(self):
        return f"0004-{self.id_cierre:08d}"


class Configuracion(models.Model):
    id_configuracion = models.AutoField(primary_key=True)
    clave = models.CharField(max_length=60, unique=True)
    valor = models.CharField(max_length=200, blank=True, default='')
    descripcion = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        db_table = 'configuracion'

    def __str__(self):
        return f'{self.clave} = {self.valor}'


class Notificacion(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    fecha = models.DateTimeField()
    tipo = models.CharField(max_length=60)
    mensaje = models.CharField(max_length=300)
    destino_perfil = models.CharField(max_length=50)
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    regla = models.CharField(max_length=40)
    entidad = models.CharField(max_length=50)
    id_registro = models.IntegerField()

    class Meta:
        db_table = 'notificacion'
        indexes = [models.Index(fields=['regla', 'entidad', 'id_registro'], name='notif_regla_registro')]

    def __str__(self):
        return f'{self.tipo}: {self.mensaje}'
