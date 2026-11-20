from django.db import migrations, models

CONFIGURACION_INICIAL = [
    ('stock_insumo_porcentaje_aviso', '100',
     'Avisar cuando el stock de un insumo llegue a este % de su stock mínimo (100 = al llegar al mínimo).'),
    ('saldo_dias_aviso', '1',
     'Días antes de la entrega para avisar de un encargo con el saldo sin cobrar.'),
    ('venta_inusual_desvios', '3',
     'Desvíos estándar sobre el promedio a partir de los cuales una venta se considera inusual.'),
    ('venta_inusual_minimo_ventas', '30',
     'Ventas previas necesarias para que la regla de venta inusual se aplique.'),
    ('perfil_stock_insumo', 'Administrador',
     'Perfil que recibe los avisos de stock bajo de insumos.'),
    ('perfil_saldo_pendiente', 'Administrador',
     'Perfil que recibe los avisos de encargos con saldo pendiente.'),
    ('perfil_venta_inusual', 'Administrador',
     'Perfil que recibe los avisos de ventas de monto inusual.'),
    ('email_destino', '',
     'Correo electrónico que recibe los avisos de las reglas marcadas.'),
    ('email_reglas', 'saldo_pendiente',
     'Reglas que además se envían por correo electrónico (separadas por coma).'),
    ('ultima_revision_diaria', '',
     'Fecha de la última revisión diaria automática (la completa el sistema).'),
]

PERMISOS_NUEVOS = [
    ('ver_reportes', 'Consultar los reportes consolidados'),
    ('ver_reporte_empleados', 'Consultar el reporte de rendición por empleado'),
    ('gestionar_configuracion', 'Modificar los parámetros de las alertas'),
]


def cargar_datos(apps, schema_editor):
    Configuracion = apps.get_model('core', 'Configuracion')
    Permiso = apps.get_model('core', 'Permiso')
    for clave, valor, descripcion in CONFIGURACION_INICIAL:
        Configuracion.objects.get_or_create(clave=clave, defaults={'valor': valor, 'descripcion': descripcion})
    for nombre, descripcion in PERMISOS_NUEVOS:
        if not Permiso.objects.filter(nombre_permiso=nombre).exists():
            Permiso.objects.create(nombre_permiso=nombre, descripcion=descripcion)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_caja_apertura'),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuracion',
            fields=[
                ('id_configuracion', models.AutoField(primary_key=True, serialize=False)),
                ('clave', models.CharField(max_length=60, unique=True)),
                ('valor', models.CharField(blank=True, default='', max_length=200)),
                ('descripcion', models.CharField(blank=True, default='', max_length=200)),
            ],
            options={
                'db_table': 'configuracion',
            },
        ),
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id_notificacion', models.AutoField(primary_key=True, serialize=False)),
                ('fecha', models.DateTimeField()),
                ('tipo', models.CharField(max_length=60)),
                ('mensaje', models.CharField(max_length=300)),
                ('destino_perfil', models.CharField(max_length=50)),
                ('leida', models.BooleanField(default=False)),
                ('fecha_lectura', models.DateTimeField(blank=True, null=True)),
                ('regla', models.CharField(max_length=40)),
                ('entidad', models.CharField(max_length=50)),
                ('id_registro', models.IntegerField()),
            ],
            options={
                'db_table': 'notificacion',
                'indexes': [models.Index(fields=['regla', 'entidad', 'id_registro'], name='notif_regla_registro')],
            },
        ),
        migrations.RunPython(cargar_datos, migrations.RunPython.noop),
    ]
