from django.db import models


class Permiso(models.Model):
    id_permiso = models.AutoField(primary_key=True)
    nombre_permiso = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'permiso'

    def __str__(self):
        return self.nombre_permiso


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    permisos = models.ManyToManyField(Permiso, through='RolPermiso', related_name='roles')

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
    id_encargo = models.AutoField(primary_key=True)
    fecha_pedido = models.DateField(blank=True, null=True)
    fecha_entrega_prevista = models.DateField(blank=True, null=True)
    senia = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=20, blank=True, null=True)
    observacion = models.CharField(max_length=200, blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING, db_column='usuario_id_usuario')
    cliente = models.ForeignKey(Cliente, on_delete=models.DO_NOTHING, db_column='cliente_id_cliente')

    class Meta:
        db_table = 'encargo'

    def __str__(self):
        return f"Encargo #{self.id_encargo}"


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

    class Meta:
        db_table = 'detalle_encargo'
        unique_together = (('producto', 'encargo'),)