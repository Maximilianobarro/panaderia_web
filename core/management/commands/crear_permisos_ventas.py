from django.core.management.base import BaseCommand

from core.models import Permiso

PERMISOS = [
    ('ver_ventas', 'Consultar ventas y ver su detalle'),
    ('registrar_venta', 'Registrar nuevas ventas'),
    ('anular_venta', 'Anular ventas y devolver el stock'),
    ('emitir_comprobante', 'Emitir el comprobante de una venta'),
]


class Command(BaseCommand):
    help = 'Crea los permisos del proceso de ventas si no existen.'

    def handle(self, *args, **options):
        for nombre, descripcion in PERMISOS:
            if Permiso.objects.filter(nombre_permiso=nombre).exists():
                self.stdout.write(f'Ya existe: {nombre}')
                continue
            Permiso.objects.create(nombre_permiso=nombre, descripcion=descripcion)
            self.stdout.write(self.style.SUCCESS(f'Creado: {nombre}'))
