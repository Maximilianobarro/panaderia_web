"""Carga los insumos de la panadería con su stock inicial, su stock mínimo y los productos que los usan.

- Solo agrega los insumos que no existen (no duplica ni modifica los que ya están).
- Renombra "Harina" a "Harina 000" (harina de panificación) y crea "Harina 0000" (pastelería):
  las medialunas y las galletas pasan a usar la 0000.
- El stock inicial se registra como un movimiento de Entrada "Stock inicial", así queda en el historial.
- Carga la receta (insumos por unidad) de cada producto que todavía no tiene receta.

Uso:
    python manage.py cargar_insumos
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.auth_utils import ROL_ADMIN
from core.models import Insumo, MovimientoInsumo, Producto, Receta, Usuario

MOTIVO = 'Stock inicial (carga de insumos)'

# Palabras para encontrar cada producto por su nombre (sin importar mayúsculas).
PRODUCTOS = {
    'medialunas': 'medialuna',
    'baguette': 'baguette',
    'chipa': 'chip',
    'tira': 'tira de pan',
    'pancho': 'pancho',
    'hamburguesa': 'hamburguesa',
    'chatas': 'chatas',
    'galletas': 'maicena',
}
PANES = ['baguette', 'tira', 'pancho', 'hamburguesa', 'chatas']

# nombre, unidad, stock inicial, stock mínimo, productos que lo usan
INSUMOS = [
    ('Harina 0000', 'kg', 300, 100, ['medialunas', 'galletas']),
    ('Manteca', 'kg', 40, 10, ['medialunas', 'galletas']),
    ('Grasa vacuna', 'kg', 30, 8, ['tira', 'chatas']),
    ('Margarina', 'kg', 25, 6, ['pancho', 'hamburguesa']),
    ('Huevos', 'unidades', 360, 90, ['medialunas', 'chipa', 'galletas', 'hamburguesa']),
    ('Leche', 'l', 40, 10, ['medialunas', 'chipa', 'hamburguesa']),
    ('Almidón de mandioca', 'kg', 25, 6, ['chipa']),
    ('Queso semiduro', 'kg', 20, 5, ['chipa']),
    ('Fécula de maíz', 'kg', 20, 5, ['galletas']),
    ('Polvo de hornear', 'kg', 5, 1, ['galletas', 'chatas']),
    ('Esencia de vainilla', 'ml', 2000, 500, ['medialunas', 'galletas']),
    ('Semillas de sésamo', 'kg', 5, 1, ['hamburguesa']),
    ('Aceite', 'l', 20, 5, ['pancho', 'hamburguesa']),
]

# Recetas estimadas para una panadería chica: cantidad de cada insumo por UNA unidad del producto.
RECETAS = {
    'medialunas': [('Harina 0000', '0.025'), ('Manteca', '0.010'), ('Azúcar', '0.004'), ('Levadura fresca', '0.001'),
                   ('Huevos', '0.05'), ('Leche', '0.006'), ('Sal', '0.0004'), ('Esencia de vainilla', '0.1')],
    'baguette': [('Harina 000', '0.160'), ('Levadura fresca', '0.003'), ('Sal', '0.003')],
    'chipa': [('Almidón de mandioca', '0.010'), ('Queso semiduro', '0.008'), ('Huevos', '0.1'), ('Leche', '0.003'),
              ('Manteca', '0.002'), ('Sal', '0.0002')],
    'tira': [('Harina 000', '0.300'), ('Levadura fresca', '0.006'), ('Sal', '0.006'), ('Grasa vacuna', '0.015')],
    'pancho': [('Harina 000', '0.035'), ('Levadura fresca', '0.001'), ('Sal', '0.0007'), ('Azúcar', '0.002'),
               ('Margarina', '0.003'), ('Aceite', '0.001')],
    'hamburguesa': [('Harina 000', '0.045'), ('Levadura fresca', '0.0015'), ('Sal', '0.0009'), ('Azúcar', '0.003'),
                    ('Margarina', '0.004'), ('Huevos', '0.05'), ('Leche', '0.008'), ('Semillas de sésamo', '0.001'),
                    ('Aceite', '0.001')],
    'chatas': [('Harina 000', '0.060'), ('Grasa vacuna', '0.010'), ('Sal', '0.001'), ('Polvo de hornear', '0.0015')],
    'galletas': [('Fécula de maíz', '0.006'), ('Harina 0000', '0.003'), ('Manteca', '0.003'),
                 ('Azúcar impalpable', '0.002'), ('Huevos', '0.03'), ('Polvo de hornear', '0.0002'),
                 ('Esencia de vainilla', '0.05')],
}

# Insumos que ya existen y están en 0: se les carga stock inicial.
STOCK_EXISTENTES = [('Azúcar', 60), ('Azúcar impalpable', 30)]


class Command(BaseCommand):
    help = 'Carga los insumos de la panadería con stock inicial, stock mínimo y productos vinculados.'

    def handle(self, *args, **options):
        usuario = (
            Usuario.objects.filter(activo=True, rol__nombre_rol=ROL_ADMIN).order_by('pk').first()
            or Usuario.objects.filter(activo=True).order_by('pk').first()
        )
        if usuario is None:
            raise CommandError('No hay usuarios activos para registrar los movimientos.')

        productos = {}
        for clave, texto in PRODUCTOS.items():
            producto = Producto.objects.filter(nombre__icontains=texto).order_by('pk').first()
            if producto is None:
                self.stdout.write(self.style.WARNING(f'No se encontró el producto «{texto}»; se omite ese vínculo.'))
            else:
                productos[clave] = producto

        ahora = timezone.now()
        with transaction.atomic():
            self._harina(productos)

            for nombre, unidad, stock, minimo, usos in INSUMOS:
                if Insumo.objects.filter(nombre__iexact=nombre).exists():
                    self.stdout.write(f'Ya existe: {nombre} (no se modifica)')
                    continue
                insumo = Insumo.objects.create(
                    nombre=nombre, unidad=unidad, stock_actual=Decimal(stock), stock_minimo=Decimal(minimo), activo=True,
                )
                MovimientoInsumo.objects.create(
                    insumo=insumo, tipo=MovimientoInsumo.TIPO_ENTRADA, cantidad=Decimal(stock),
                    stock_resultante=insumo.stock_actual, fecha_hora=ahora, motivo=MOTIVO, usuario=usuario,
                )
                insumo.productos.add(*[productos[u] for u in usos if u in productos])
                self.stdout.write(self.style.SUCCESS(f'Creado: {nombre} ({stock} {unidad}, mínimo {minimo})'))

            for nombre, cantidad in STOCK_EXISTENTES:
                insumo = Insumo.objects.select_for_update().filter(nombre__iexact=nombre).first()
                if insumo is None:
                    self.stdout.write(self.style.WARNING(f'No existe «{nombre}»; no se carga stock.'))
                    continue
                if insumo.stock_actual > 0:
                    self.stdout.write(f'{nombre} ya tiene stock ({insumo.stock_actual}); no se modifica.')
                    continue
                insumo.stock_actual += Decimal(cantidad)
                insumo.save(update_fields=['stock_actual'])
                MovimientoInsumo.objects.create(
                    insumo=insumo, tipo=MovimientoInsumo.TIPO_ENTRADA, cantidad=Decimal(cantidad),
                    stock_resultante=insumo.stock_actual, fecha_hora=ahora, motivo=MOTIVO, usuario=usuario,
                )
                self.stdout.write(self.style.SUCCESS(f'Stock inicial: {nombre} +{cantidad} {insumo.unidad}'))

            self._recetas(productos)

        self.stdout.write(self.style.SUCCESS('Carga de insumos terminada.'))

    def _recetas(self, productos):
        """Carga la receta de cada producto que todavía no tiene ninguna."""
        for clave, lineas in RECETAS.items():
            producto = productos.get(clave)
            if producto is None:
                continue
            if Receta.objects.filter(producto=producto).exists():
                self.stdout.write(f'Ya tiene receta: {producto.nombre} (no se modifica)')
                continue
            cargadas = 0
            for nombre, cantidad in lineas:
                insumo = Insumo.objects.filter(nombre__iexact=nombre).first()
                if insumo is None:
                    self.stdout.write(self.style.WARNING(f'Receta de {producto.nombre}: no existe «{nombre}», se omite.'))
                    continue
                Receta.objects.create(producto=producto, insumo=insumo, cantidad=Decimal(cantidad))
                insumo.productos.add(producto)
                cargadas += 1
            self.stdout.write(self.style.SUCCESS(f'Receta cargada: {producto.nombre} ({cargadas} insumos)'))

    def _harina(self, productos):
        """Renombra "Harina" a "Harina 000" y la deja vinculada a los panes (las facturas usan la 0000)."""
        if Insumo.objects.filter(nombre__iexact='Harina 000').exists():
            self.stdout.write('Ya existe: Harina 000 (no se modifica)')
            return
        harina = Insumo.objects.filter(nombre__iexact='Harina').first()
        if harina is None:
            self.stdout.write(self.style.WARNING('No existe «Harina» para renombrar; se crea «Harina 000».'))
            harina = Insumo.objects.create(nombre='Harina 000', unidad='kg', stock_actual=Decimal('0'),
                                           stock_minimo=Decimal('500'), activo=True)
        else:
            harina.nombre = 'Harina 000'
            harina.save(update_fields=['nombre'])
            self.stdout.write(self.style.SUCCESS('Renombrado: Harina → Harina 000'))
        harina.productos.add(*[productos[p] for p in PANES if p in productos])
        harina.productos.remove(*[productos[p] for p in ('medialunas', 'galletas') if p in productos])
