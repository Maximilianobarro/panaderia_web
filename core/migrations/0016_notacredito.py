import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_insumo_movimientoinsumo'),
    ]

    operations = [
        migrations.CreateModel(
            name='NotaCredito',
            fields=[
                ('id_nota_credito', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_hora', models.DateTimeField()),
                ('monto', models.DecimalField(decimal_places=2, max_digits=12)),
                ('medio_devolucion', models.CharField(max_length=30)),
                ('motivo', models.CharField(max_length=200)),
                ('encargo', models.OneToOneField(db_column='encargo_id_encargo', on_delete=django.db.models.deletion.DO_NOTHING, related_name='nota_credito', to='core.encargo')),
                ('usuario', models.ForeignKey(db_column='usuario_id_usuario', on_delete=django.db.models.deletion.DO_NOTHING, related_name='notas_credito', to='core.usuario')),
            ],
            options={
                'db_table': 'nota_credito',
            },
        ),
    ]
