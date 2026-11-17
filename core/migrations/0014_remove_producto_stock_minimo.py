from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_producto_stock_minimo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producto',
            name='stock_minimo',
        ),
    ]
