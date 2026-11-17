import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_reponer_stock_encargos_pendientes'),
    ]

    operations = [
        migrations.AddField(
            model_name='encargo',
            name='fecha_pago_saldo',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='encargo',
            name='medio_pago_saldo',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='encargo',
            name='usuario_pago_saldo',
            field=models.ForeignKey(blank=True, db_column='usuario_pago_saldo_id_usuario', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='saldos_cobrados', to='core.usuario'),
        ),
    ]
