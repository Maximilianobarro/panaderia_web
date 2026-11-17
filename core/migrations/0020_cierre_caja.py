from datetime import datetime, timedelta, timezone

import django.db.models.deletion
from django.db import migrations, models

ZONA_LOCAL = timezone(timedelta(hours=-3))


def completar_hora_registro(apps, schema_editor):
    Encargo = apps.get_model('core', 'Encargo')
    for e in Encargo.objects.filter(fecha_hora_registro=None).exclude(fecha_pedido=None):
        f = e.fecha_pedido
        Encargo.objects.filter(pk=e.pk).update(fecha_hora_registro=datetime(f.year, f.month, f.day, tzinfo=ZONA_LOCAL))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_encargo_pago_saldo'),
    ]

    operations = [
        migrations.AddField(
            model_name='encargo',
            name='fecha_hora_registro',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(completar_hora_registro, migrations.RunPython.noop),
        migrations.CreateModel(
            name='CierreCaja',
            fields=[
                ('id_cierre', models.AutoField(primary_key=True, serialize=False)),
                ('desde', models.DateTimeField()),
                ('hasta', models.DateTimeField()),
                ('cantidad_ventas', models.IntegerField(default=0)),
                ('total_ventas', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_senias', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_saldos', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_devoluciones', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('efectivo', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('transferencia', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('tarjeta', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('total_turno', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('observacion', models.CharField(blank=True, max_length=200, null=True)),
                ('usuario', models.ForeignKey(db_column='usuario_id_usuario', on_delete=django.db.models.deletion.DO_NOTHING, related_name='cierres_caja', to='core.usuario')),
            ],
            options={
                'db_table': 'cierre_caja',
            },
        ),
    ]
