from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_detalleencargo_preparado'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='stock_minimo',
            field=models.IntegerField(default=0),
        ),
    ]
