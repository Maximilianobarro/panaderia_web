import json
from datetime import datetime, time, timedelta

from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import permiso_requerido
from .models import LogAuditoria, Usuario

PERMISO_AUDITORIA = 'ver_auditoria'
MAX_FILAS = 300


def _parse_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _inicio_dia(fecha):
    return timezone.make_aware(datetime.combine(fecha, time.min))


def _leer(texto):
    if not texto:
        return {}
    try:
        datos = json.loads(texto)
    except ValueError:
        return {}
    return datos if isinstance(datos, dict) else {}


def _cambios(log):
    antes = _leer(log.valores_anteriores)
    despues = _leer(log.valores_actuales)
    campos = list(antes) + [c for c in despues if c not in antes]
    return [
        {'campo': c, 'antes': antes.get(c, '-'), 'despues': despues.get(c, '-')}
        for c in campos
    ]


@permiso_requerido(PERMISO_AUDITORIA)
@require_http_methods(['GET'])
def auditoria_lista(request):
    errores = []
    desde_txt = request.GET.get('desde', '').strip()
    hasta_txt = request.GET.get('hasta', '').strip()
    entidad = request.GET.get('entidad', '').strip()
    accion = request.GET.get('accion', '').strip()
    usuario_id = request.GET.get('usuario', '').strip()

    desde = _parse_fecha(desde_txt) if desde_txt else None
    hasta = _parse_fecha(hasta_txt) if hasta_txt else None
    if desde_txt and desde is None:
        errores.append('La fecha "desde" no es válida.')
    if hasta_txt and hasta is None:
        errores.append('La fecha "hasta" no es válida.')
    if desde and hasta and desde > hasta:
        errores.append('La fecha "desde" no puede ser posterior a "hasta".')
        desde = hasta = None

    logs = LogAuditoria.objects.select_related('usuario')
    if desde:
        logs = logs.filter(fecha_hora__gte=_inicio_dia(desde))
    if hasta:
        logs = logs.filter(fecha_hora__lt=_inicio_dia(hasta + timedelta(days=1)))
    if entidad:
        logs = logs.filter(entidad=entidad)
    if accion:
        logs = logs.filter(accion=accion)
    if usuario_id.isdecimal():
        logs = logs.filter(usuario_id=int(usuario_id))

    total = logs.count()
    filas = list(logs.order_by('-fecha_hora', '-id_log')[:MAX_FILAS])
    for fila in filas:
        fila.cambios = _cambios(fila)

    return render(request, 'core/auditoria_lista.html', {
        'filas': filas,
        'total': total,
        'max_filas': MAX_FILAS,
        'errores': errores,
        'entidades': LogAuditoria.objects.order_by().values_list('entidad', flat=True).distinct(),
        'acciones': ['MODIFICACION', 'ANULACION', 'ELIMINACION'],
        'usuarios': Usuario.objects.order_by('nombre_usuario'),
        'filtros': {
            'desde': desde_txt,
            'hasta': hasta_txt,
            'entidad': entidad,
            'accion': accion,
            'usuario': usuario_id,
        },
    })
