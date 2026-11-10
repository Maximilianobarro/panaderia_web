from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_activo_rol_permiso_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='detalleencargo',
            name='preparado',
            field=models.BooleanField(default=False),
        ),
    ]
