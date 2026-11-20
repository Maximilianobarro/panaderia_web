from django.db import migrations, models
from django.db.models import F


def completar_esperado(apps, schema_editor):
    CierreCaja = apps.get_model('core', 'CierreCaja')
    CierreCaja.objects.all().update(efectivo_esperado=F('efectivo'))


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_cierre_caja'),
    ]

    operations = [
        migrations.AddField(
            model_name='cierrecaja',
            name='estado',
            field=models.CharField(default='Cerrada', max_length=20),
        ),
        migrations.AddField(
            model_name='cierrecaja',
            name='fondo_inicial',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='cierrecaja',
            name='efectivo_esperado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='cierrecaja',
            name='hasta',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(completar_esperado, migrations.RunPython.noop),
    ]
