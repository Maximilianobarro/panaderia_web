from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_rol_permisos'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producto',
            name='unidad_medida',
        ),
    ]