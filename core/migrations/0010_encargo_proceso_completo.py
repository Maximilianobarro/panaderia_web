import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_encargo_cantidad_items_medio_pago'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='encargo',
            name='cantidad_items',
        ),
        migrations.AddField(
            model_name='encargo',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='encargo',
            name='fecha_entrega_real',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='encargo',
            name='fecha_anulacion',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='encargo',
            name='motivo_anulacion',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='encargo',
            name='usuario_anulacion',
            field=models.ForeignKey(blank=True, db_column='usuario_anulacion_id_usuario', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='encargos_anulados', to='core.usuario'),
        ),
    ]
