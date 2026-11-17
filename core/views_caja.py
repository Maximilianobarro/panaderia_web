from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import ROL_ADMIN, permiso_requerido
from .models import CierreCaja, Encargo, NotaCredito, Usuario, Venta
from .views_hito3 import ESTADO_CONFIRMADA, MEDIOS_PAGO, ZONA_LOCAL, _hoy, _parse_fecha, _usuario_actual

PERMISO_CAJA = 'cierre_caja'
SIN_DATO = 'Sin dato'
TIPOS = [
    ('ventas', 'Ventas'),
    ('senias', 'Señas de encargos'),
    ('saldos', 'Saldos de encargos'),
    ('devoluciones', 'Devoluciones (notas de crédito)'),
]
MAX_TEXTO = 200


def _es_admin(usuario):
    return usuario.rol.nombre_rol == ROL_ADMIN


def _texto(dt):
    return dt.astimezone(ZONA_LOCAL).strftime('%d/%m/%Y %H:%M')


def _medio(valor):
    return valor if valor in MEDIOS_PAGO else SIN_DATO


def _inicio_turno(usuario):
    ultimo = CierreCaja.objects.filter(usuario=usuario).order_by('-hasta').first()
    if ultimo is not None:
        return ultimo.hasta
    hoy = _hoy()
    return datetime(hoy.year, hoy.month, hoy.day, tzinfo=ZONA_LOCAL)


def _calcular(usuario, desde, hasta):
    medios = MEDIOS_PAGO + [SIN_DATO]
    detalle = {clave: {m: Decimal('0') for m in medios} for clave, _ in TIPOS}
    ventas = Venta.objects.filter(
        usuario=usuario, estado=ESTADO_CONFIRMADA, fecha_hora__gt=desde, fecha_hora__lte=hasta,
    )
    cantidad_ventas = 0
    for v in ventas:
        detalle['ventas'][_medio(v.medio_pago)] += v.total
        cantidad_ventas += 1
    for e in Encargo.objects.filter(usuario=usuario, fecha_hora_registro__gt=desde, fecha_hora_registro__lte=hasta):
        if e.senia:
            detalle['senias'][_medio(e.medio_pago)] += e.senia
    for e in Encargo.objects.filter(usuario_pago_saldo=usuario, fecha_pago_saldo__gt=desde, fecha_pago_saldo__lte=hasta):
        detalle['saldos'][_medio(e.medio_pago_saldo)] += e.saldo
    for n in NotaCredito.objects.filter(usuario=usuario, fecha_hora__gt=desde, fecha_hora__lte=hasta):
        detalle['devoluciones'][_medio(n.medio_devolucion)] += n.monto
    totales = {clave: sum(detalle[clave].values(), Decimal('0')) for clave, _ in TIPOS}
    por_medio = {
        m: detalle['ventas'][m] + detalle['senias'][m] + detalle['saldos'][m] - detalle['devoluciones'][m]
        for m in medios
    }
    filas = [
        {'nombre': nombre, 'signo': '−' if clave == 'devoluciones' else '', 'importes': [detalle[clave][m] for m in medios], 'total': totales[clave]}
        for clave, nombre in TIPOS
    ]
    return {
        'medios': medios,
        'filas': filas,
        'cantidad_ventas': cantidad_ventas,
        'totales': totales,
        'por_medio': por_medio,
        'neto_medios': [por_medio[m] for m in medios],
        'total_turno': totales['ventas'] + totales['senias'] + totales['saldos'] - totales['devoluciones'],
    }


@permiso_requerido(PERMISO_CAJA)
@require_http_methods(['GET', 'POST'])
def caja_cerrar(request):
    usuario = _usuario_actual(request)
    if _es_admin(usuario):
        messages.error(request, 'El Administrador no cierra caja: puede ver los cierres de todos los empleados.')
        return redirect('caja_lista')

    if request.method == 'POST':
        observacion = request.POST.get('observacion', '').strip()
        if len(observacion) > MAX_TEXTO:
            messages.error(request, f'La observación no puede superar {MAX_TEXTO} caracteres.')
            return redirect('caja_cerrar')
        with transaction.atomic():
            Usuario.objects.select_for_update().get(pk=usuario.pk)
            desde = _inicio_turno(usuario)
            hasta = timezone.now()
            datos = _calcular(usuario, desde, hasta)
            cierre = CierreCaja.objects.create(
                usuario=usuario,
                desde=desde,
                hasta=hasta,
                cantidad_ventas=datos['cantidad_ventas'],
                total_ventas=datos['totales']['ventas'],
                total_senias=datos['totales']['senias'],
                total_saldos=datos['totales']['saldos'],
                total_devoluciones=datos['totales']['devoluciones'],
                efectivo=datos['por_medio']['Efectivo'],
                transferencia=datos['por_medio']['Transferencia'],
                tarjeta=datos['por_medio']['Tarjeta'],
                total_turno=datos['total_turno'],
                observacion=observacion or None,
            )
        messages.success(request, f'Caja cerrada. Cierre {cierre.numero_comprobante} registrado.')
        return redirect('caja_comprobante', pk=cierre.pk)

    desde = _inicio_turno(usuario)
    hasta = timezone.now()
    return render(request, 'core/caja_cerrar.html', {
        'datos': _calcular(usuario, desde, hasta),
        'desde_txt': _texto(desde),
        'hasta_txt': _texto(hasta),
    })


@permiso_requerido(PERMISO_CAJA)
@require_http_methods(['GET'])
def caja_lista(request):
    usuario = _usuario_actual(request)
    es_admin = _es_admin(usuario)
    fecha_txt = request.GET.get('fecha', '').strip()
    fecha = _parse_fecha(fecha_txt) if fecha_txt else _hoy()
    if fecha is None:
        messages.error(request, 'La fecha no es válida.')
        fecha = _hoy()
    empleado_id = request.GET.get('empleado', '').strip()

    inicio = datetime(fecha.year, fecha.month, fecha.day, tzinfo=ZONA_LOCAL)
    cierres = CierreCaja.objects.select_related('usuario').filter(
        hasta__gte=inicio, hasta__lt=inicio + timedelta(days=1),
    )
    if not es_admin:
        cierres = cierres.filter(usuario=usuario)
    elif empleado_id.isdecimal():
        cierres = cierres.filter(usuario_id=int(empleado_id))
    cierres = list(cierres.order_by('-hasta'))
    for c in cierres:
        c.desde_txt = _texto(c.desde)
        c.hasta_txt = _texto(c.hasta)

    campos = ['total_ventas', 'total_senias', 'total_saldos', 'total_devoluciones', 'efectivo', 'transferencia', 'tarjeta', 'total_turno']
    total_dia = {campo: sum((getattr(c, campo) for c in cierres), Decimal('0')) for campo in campos}
    total_dia['cantidad_ventas'] = sum(c.cantidad_ventas for c in cierres)

    return render(request, 'core/caja_lista.html', {
        'cierres': cierres,
        'total_dia': total_dia,
        'es_admin_caja': es_admin,
        'empleados': Usuario.objects.filter(cierres_caja__isnull=False).distinct().order_by('nombre_usuario') if es_admin else [],
        'filtros': {'fecha': fecha.isoformat(), 'empleado': empleado_id},
        'fecha_txt': fecha.strftime('%d/%m/%Y'),
    })


@permiso_requerido(PERMISO_CAJA)
@require_http_methods(['GET'])
def caja_comprobante(request, pk):
    usuario = _usuario_actual(request)
    cierre = get_object_or_404(CierreCaja.objects.select_related('usuario'), pk=pk)
    if not _es_admin(usuario) and cierre.usuario_id != usuario.pk:
        messages.error(request, 'Solo podés ver tus propios cierres de caja.')
        return redirect('caja_lista')
    return render(request, 'core/caja_comprobante.html', {
        'cierre': cierre,
        'datos': _calcular(cierre.usuario, cierre.desde, cierre.hasta),
        'desde_txt': _texto(cierre.desde),
        'hasta_txt': _texto(cierre.hasta),
    })
