from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_encargo_proceso_completo'),
    ]

    operations = [
        migrations.AddField(
            model_name='permiso',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='rol',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='categoria',
            name='activo',
            field=models.BooleanField(default=True),
        ),
    ]
