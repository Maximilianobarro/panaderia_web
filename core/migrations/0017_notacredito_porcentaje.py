from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_notacredito'),
    ]

    operations = [
        migrations.AddField(
            model_name='notacredito',
            name='porcentaje',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
