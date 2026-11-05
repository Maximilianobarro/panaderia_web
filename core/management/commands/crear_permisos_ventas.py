from django.core.management.base import BaseCommand

from core.models import Permiso

PERMISOS = [
    ('ver_ventas', 'Consultar ventas y ver su detalle'),
    ('registrar_venta', 'Registrar nuevas ventas'),
    ('emitir_comprobante', 'Emitir el comprobante de una venta'),
    ('ver_auditoria', 'Consultar el registro de auditoría'),
    ('cancelar_encargo', 'Cancelar encargos pendientes'),
]


class Command(BaseCommand):
    help = 'Crea los permisos de ventas, encargos y auditoría si no existen.'

    def handle(self, *args, **options):
        for nombre, descripcion in PERMISOS:
            if Permiso.objects.filter(nombre_permiso=nombre).exists():
                self.stdout.write(f'Ya existe: {nombre}')
                continue
            Permiso.objects.create(nombre_permiso=nombre, descripcion=descripcion)
            self.stdout.write(self.style.SUCCESS(f'Creado: {nombre}'))
