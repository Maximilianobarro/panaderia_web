from django.db import migrations
from django.db.models import F


def reponer(apps, schema_editor):
    DetalleEncargo = apps.get_model('core', 'DetalleEncargo')
    Producto = apps.get_model('core', 'Producto')
    for d in DetalleEncargo.objects.filter(encargo__estado='Pendiente'):
        Producto.objects.filter(pk=d.producto_id).update(stock_actual=F('stock_actual') + d.cantidad)


def descontar(apps, schema_editor):
    DetalleEncargo = apps.get_model('core', 'DetalleEncargo')
    Producto = apps.get_model('core', 'Producto')
    for d in DetalleEncargo.objects.filter(encargo__estado='Pendiente'):
        Producto.objects.filter(pk=d.producto_id).update(stock_actual=F('stock_actual') - d.cantidad)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_notacredito_porcentaje'),
    ]

    operations = [
        migrations.RunPython(reponer, descontar),
    ]
