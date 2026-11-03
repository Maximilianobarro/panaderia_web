from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_cliente_activo_logauditoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='encargo',
            name='cantidad_items',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='encargo',
            name='medio_pago',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
