import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_remove_producto_stock_minimo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Insumo',
            fields=[
                ('id_insumo', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=80)),
                ('unidad', models.CharField(max_length=20)),
                ('stock_actual', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('stock_minimo', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('activo', models.BooleanField(default=True)),
                ('productos', models.ManyToManyField(blank=True, db_table='insumo_producto', related_name='insumos', to='core.producto')),
            ],
            options={
                'db_table': 'insumo',
            },
        ),
        migrations.CreateModel(
            name='MovimientoInsumo',
            fields=[
                ('id_movimiento', models.AutoField(primary_key=True, serialize=False)),
                ('tipo', models.CharField(max_length=20)),
                ('cantidad', models.DecimalField(decimal_places=3, max_digits=12)),
                ('stock_resultante', models.DecimalField(decimal_places=3, max_digits=12)),
                ('fecha_hora', models.DateTimeField()),
                ('motivo', models.CharField(max_length=200)),
                ('insumo', models.ForeignKey(db_column='insumo_id_insumo', on_delete=django.db.models.deletion.DO_NOTHING, related_name='movimientos', to='core.insumo')),
                ('usuario', models.ForeignKey(db_column='usuario_id_usuario', on_delete=django.db.models.deletion.DO_NOTHING, related_name='movimientos_insumo', to='core.usuario')),
            ],
            options={
                'db_table': 'movimiento_insumo',
            },
        ),
    ]
