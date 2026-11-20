"""Carga datos de prueba realistas para el módulo de analítica y los reportes.

Genera ventas, encargos (entregados, cancelados con nota de crédito y
pendientes) y cierres de caja para los últimos N días, usando los modelos
del propio sistema. Simula el ritmo de una panadería: más movimiento a la
mañana temprano y a la tarde, y más los fines de semana.

IMPORTANTE: hacer una copia de seguridad de la base antes de correrlo.
El sistema no borra registros, así que la única forma de deshacer la carga
es restaurar esa copia.

Uso:
    python manage.py cargar_datos_prueba --dias 90
"""
import random
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.auth_utils import ROL_ADMIN
from core.models import (
    CierreCaja, Cliente, Configuracion, DetalleEncargo, DetalleVenta, Encargo, NotaCredito, Producto, Usuario, Venta,
)
from core.views_caja import _calcular
from core.views_hito3 import ESTADO_CONFIRMADA, ZONA_LOCAL, _hoy

CLAVE_CARGA = 'datos_prueba_cargados'

# Peso de cada hora de atención (7 a 20 h): picos a la mañana y a la tarde.
PESO_HORA = {7: 6, 8: 10, 9: 9, 10: 6, 11: 4, 12: 4, 13: 3, 14: 3, 15: 4, 16: 6, 17: 9, 18: 10, 19: 8, 20: 4}
# Lunes = 0 ... Domingo = 6
FACTOR_DIA = {0: 0.9, 1: 0.9, 2: 1.0, 3: 1.0, 4: 1.2, 5: 1.5, 6: 1.2}
PESO_MEDIO = {'Efectivo': 5, 'Transferencia': 3, 'Tarjeta': 2}
VENTAS_POR_DIA = 22

CLIENTES_PRUEBA = [
    ('Lucía', 'Guzmán'), ('Martín', 'Aramayo'), ('Sofía', 'Cruz'), ('Diego', 'Mamaní'),
    ('Valentina', 'Choque'), ('Joaquín', 'Ríos'), ('Camila', 'Farfán'), ('Tomás', 'Vilte'),
    ('Florencia', 'Quispe'), ('Nicolás', 'Burgos'),
]


def _plata(valor):
    return Decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = 'Carga ventas, encargos y cierres de caja de prueba para los últimos N días (hacer backup antes).'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=90, help='Cantidad de días hacia atrás (por defecto 90).')
        parser.add_argument('--semilla', type=int, default=2026, help='Semilla aleatoria, para poder repetir la carga.')
        parser.add_argument('--forzar', action='store_true', help='Cargar aunque ya se hayan cargado datos de prueba.')

    def handle(self, *args, **opciones):
        dias = opciones['dias']
        if not 7 <= dias <= 365:
            raise CommandError('--dias debe estar entre 7 y 365.')
        marca = Configuracion.objects.filter(clave=CLAVE_CARGA).first()
        if marca is not None and marca.valor and not opciones['forzar']:
            raise CommandError(f'Ya se cargaron datos de prueba ({marca.valor}). Usá --forzar para cargar otra vez.')

        self.azar = random.Random(opciones['semilla'])
        self._preparar()
        if CierreCaja.objects.filter(estado=CierreCaja.ESTADO_ABIERTA, desde__lt=self._momento(_hoy(), 0)).exists():
            self.stdout.write(self.style.WARNING(
                'Aviso: hay cajas abiertas desde antes de hoy; sus totales van a incluir datos de prueba.'
            ))

        hoy = _hoy()
        self.inicio = hoy - timedelta(days=dias)
        self.dias = dias
        resumen = {'ventas': 0, 'entregados': 0, 'cancelados': 0, 'pendientes': 0, 'cajas': 0}
        with transaction.atomic():
            for i in range(dias, 0, -1):
                self._cargar_dia(hoy - timedelta(days=i), resumen)
            texto = (f'{timezone.now().astimezone(ZONA_LOCAL):%d/%m/%Y %H:%M}: {dias} días, '
                     f'{resumen["ventas"]} ventas, {resumen["entregados"] + resumen["cancelados"] + resumen["pendientes"]} encargos')
            Configuracion.objects.update_or_create(
                clave=CLAVE_CARGA, defaults={'valor': texto, 'descripcion': 'Registro de la carga de datos de prueba.'},
            )

        self.stdout.write(self.style.SUCCESS('Datos de prueba cargados.'))
        self.stdout.write(
            f'- Ventas: {resumen["ventas"]}\n'
            f'- Encargos: {resumen["entregados"]} entregados, {resumen["cancelados"]} cancelados '
            f'(con nota de crédito), {resumen["pendientes"]} pendientes\n'
            f'- Cierres de caja: {resumen["cajas"]}\n'
            'El stock de los productos no se modificó (son ventas históricas de prueba).'
        )

    # ---------- Preparación ----------

    def _preparar(self):
        self.productos = list(Producto.objects.filter(estado__iexact='activo').order_by('pk'))
        if not self.productos:
            raise CommandError('No hay productos activos.')
        # Popularidad: algunos productos se venden mucho más que otros.
        self.peso_producto = [1 / (i + 1) ** 0.8 for i in range(len(self.productos))]
        self.azar.shuffle(self.peso_producto)

        usuarios = list(Usuario.objects.filter(activo=True).select_related('rol').order_by('pk'))
        self.empleados = [u for u in usuarios if u.rol.nombre_rol != ROL_ADMIN] or usuarios
        if not self.empleados:
            raise CommandError('No hay usuarios activos.')

        self.consumidor_final = Cliente.objects.filter(nombre__iexact='Consumidor', apellido__iexact='Final').first()
        clientes = [
            c for c in Cliente.objects.filter(activo=True).order_by('pk')
            if self.consumidor_final is None or c.pk != self.consumidor_final.pk
        ]
        if len(clientes) < 8:
            for nombre, apellido in CLIENTES_PRUEBA:
                if not Cliente.objects.filter(nombre=nombre, apellido=apellido).exists():
                    clientes.append(Cliente.objects.create(
                        nombre=nombre, apellido=apellido, fecha_alta=_hoy(), activo=True,
                    ))
            self.stdout.write('Se crearon clientes de prueba (había menos de 8 clientes activos).')
        self.clientes = clientes
        # Pocos clientes concentran la mayor parte de las compras.
        self.peso_cliente = [1 / (i + 1) for i in range(len(self.clientes))]

    # ---------- Utilidades ----------

    def _momento(self, fecha, hora, minuto=0):
        return datetime.combine(fecha, time(hora, minuto), tzinfo=ZONA_LOCAL)

    def _hora_al_azar(self, fecha, desde, hasta):
        horas = [h for h in PESO_HORA if desde <= h < hasta]
        hora = self.azar.choices(horas, weights=[PESO_HORA[h] for h in horas])[0]
        return self._momento(fecha, hora, self.azar.randint(0, 59))

    def _medio(self):
        return self.azar.choices(list(PESO_MEDIO), weights=list(PESO_MEDIO.values()))[0]

    def _cliente_venta(self):
        if self.consumidor_final is not None and self.azar.random() < 0.75:
            return self.consumidor_final
        return self.azar.choices(self.clientes, weights=self.peso_cliente)[0]

    def _productos(self, cantidad):
        elegidos = set()
        while len(elegidos) < min(cantidad, len(self.productos)):
            elegidos.add(self.azar.choices(range(len(self.productos)), weights=self.peso_producto)[0])
        return [self.productos[i] for i in sorted(elegidos)]

    # ---------- Un día de trabajo ----------

    def _turnos(self, fecha):
        """Turnos del día: mañana (7 a 14 h) y tarde (14 a 21 h), rotando entre los empleados."""
        indice = (fecha - self.inicio).days
        n = len(self.empleados)
        return [
            (self.empleados[(2 * indice) % n], 7, 14),
            (self.empleados[(2 * indice + 1) % n], 14, 21),
        ]

    def _empleado_en(self, momento):
        return next(u for u, desde, hasta in self._turnos(momento.date()) if desde <= momento.hour < hasta)

    def _cargar_dia(self, fecha, resumen):
        turnos = self._turnos(fecha)
        indice = (fecha - self.inicio).days
        tendencia = 0.85 + 0.3 * indice / max(self.dias - 1, 1)  # el negocio crece de a poco
        cantidad = max(1, round(VENTAS_POR_DIA * FACTOR_DIA[fecha.weekday()] * tendencia * self.azar.uniform(0.8, 1.2)))

        for _ in range(cantidad):
            momento = self._hora_al_azar(fecha, 7, 21)
            self._crear_venta(momento, self._empleado_en(momento))
            resumen['ventas'] += 1

        for _ in range(self.azar.choices([0, 1, 2], weights=[3, 5, 2])[0]):
            momento = self._hora_al_azar(fecha, 8, 19)
            resumen[self._crear_encargo(momento, self._empleado_en(momento))] += 1

        # Cierres de caja de cada turno, calculados igual que en la pantalla de Caja.
        for empleado, desde, hasta in turnos:
            inicio = self._momento(fecha, desde)
            fin = self._momento(fecha, hasta - 1, 59)
            datos = _calcular(empleado, inicio, fin)
            if not datos['total_turno'] and not datos['cantidad_ventas']:
                continue
            CierreCaja.objects.create(
                usuario=empleado, estado=CierreCaja.ESTADO_CERRADA, desde=inicio, hasta=fin,
                cantidad_ventas=datos['cantidad_ventas'],
                total_ventas=datos['totales']['ventas'], total_senias=datos['totales']['senias'],
                total_saldos=datos['totales']['saldos'], total_devoluciones=datos['totales']['devoluciones'],
                efectivo=datos['por_medio']['Efectivo'], transferencia=datos['por_medio']['Transferencia'],
                tarjeta=datos['por_medio']['Tarjeta'], total_turno=datos['total_turno'],
                efectivo_esperado=datos['por_medio']['Efectivo'],
            )
            resumen['cajas'] += 1

    def _crear_venta(self, momento, empleado):
        grande = self.azar.random() < 0.01  # alguna compra grande cada tanto
        productos = self._productos(self.azar.choices([1, 2, 3, 4], weights=[4, 4, 2, 1])[0])
        venta = Venta.objects.create(
            fecha_hora=momento, medio_pago=self._medio(), estado=ESTADO_CONFIRMADA,
            usuario=empleado, cliente=self._cliente_venta(), total=Decimal('0'),
        )
        detalles, total = [], Decimal('0')
        for producto in productos:
            cantidad = self.azar.randint(20, 40) if grande else self.azar.choices(
                range(1, 13), weights=[8, 9, 6, 6, 3, 6, 2, 2, 1, 2, 1, 3])[0]
            subtotal = producto.precio_unitario * cantidad
            detalles.append(DetalleVenta(
                venta=venta, producto=producto, cantidad=cantidad,
                precio_unitario_venta=producto.precio_unitario, subtotal=subtotal,
            ))
            total += subtotal
        DetalleVenta.objects.bulk_create(detalles)
        venta.total = total
        venta.save(update_fields=['total'])

    def _crear_encargo(self, momento, empleado):
        hoy = _hoy()
        fecha_pedido = momento.date()
        entrega = fecha_pedido + timedelta(days=self.azar.randint(1, 5))
        productos = self._productos(self.azar.choices([1, 2, 3], weights=[4, 4, 2])[0])
        lineas = [(p, self.azar.choice([6, 12, 12, 24, 24, 36])) for p in productos]
        total = sum((p.precio_unitario * c for p, c in lineas), Decimal('0'))
        senia = min(total, _plata(total * Decimal(str(self.azar.choice([0.5, 0.5, 0.6, 0.7, 1.0])))))
        medio = self._medio()

        datos = dict(
            fecha_pedido=fecha_pedido, fecha_hora_registro=momento, fecha_entrega_prevista=entrega,
            senia=senia, total=total, medio_pago=medio, usuario=empleado,
            cliente=self.azar.choices(self.clientes, weights=self.peso_cliente)[0],
        )
        if entrega >= hoy:
            resultado = 'pendientes'
            datos['estado'] = Encargo.ESTADO_PENDIENTE
        elif self.azar.random() < 0.12:
            resultado = 'cancelados'
            # El cliente cancela el mismo día, antes de que se empiece a preparar.
            anulacion = min(momento + timedelta(minutes=self.azar.randint(30, 120)), self._momento(fecha_pedido, 20, 50))
            datos.update(
                estado=Encargo.ESTADO_CANCELADO, fecha_anulacion=anulacion,
                motivo_anulacion='El cliente canceló el pedido.', usuario_anulacion=self._empleado_en(anulacion),
            )
        else:
            resultado = 'entregados'
            pago = self._momento(entrega, self.azar.randint(9, 19), self.azar.randint(0, 59))
            datos.update(estado=Encargo.ESTADO_ENTREGADO, fecha_entrega_real=pago + timedelta(minutes=5))
            if total > senia:
                datos.update(
                    fecha_pago_saldo=pago, medio_pago_saldo=self._medio(), usuario_pago_saldo=self._empleado_en(pago),
                )

        encargo = Encargo.objects.create(**datos)
        DetalleEncargo.objects.bulk_create([
            DetalleEncargo(
                encargo=encargo, producto=p, cantidad=c, precio_unitario=p.precio_unitario,
                subtotal=p.precio_unitario * c, preparado=(resultado == 'entregados'),
            )
            for p, c in lineas
        ])
        if resultado == 'cancelados' and senia > 0:
            # Cancelado antes de empezar la preparación: se devuelve el 100 % de la seña.
            NotaCredito.objects.create(
                encargo=encargo, fecha_hora=datos['fecha_anulacion'], monto=senia, porcentaje=Decimal('100'),
                medio_devolucion=medio, motivo=datos['motivo_anulacion'], usuario=datos['usuario_anulacion'],
            )
        return resultado
