import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_alertas_por_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='Produccion',
            fields=[
                ('id_produccion', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.IntegerField()),
                ('fecha_hora', models.DateTimeField()),
                ('producto', models.ForeignKey(db_column='producto_id_producto', on_delete=django.db.models.deletion.DO_NOTHING, related_name='producciones', to='core.producto')),
                ('usuario', models.ForeignKey(db_column='usuario_id_usuario', on_delete=django.db.models.deletion.DO_NOTHING, related_name='producciones', to='core.usuario')),
            ],
            options={
                'db_table': 'produccion',
            },
        ),
        migrations.CreateModel(
            name='Receta',
            fields=[
                ('id_receta', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.DecimalField(decimal_places=4, max_digits=12)),
                ('insumo', models.ForeignKey(db_column='insumo_id_insumo', on_delete=django.db.models.deletion.DO_NOTHING, related_name='recetas', to='core.insumo')),
                ('producto', models.ForeignKey(db_column='producto_id_producto', on_delete=django.db.models.deletion.DO_NOTHING, related_name='receta', to='core.producto')),
            ],
            options={
                'db_table': 'receta',
                'unique_together': {('producto', 'insumo')},
            },
        ),
        migrations.AddField(
            model_name='movimientoinsumo',
            name='produccion',
            field=models.ForeignKey(blank=True, db_column='produccion_id_produccion', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='movimientos', to='core.produccion'),
        ),
    ]
