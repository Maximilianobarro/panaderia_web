import json
import re
from datetime import datetime, time, timedelta

from django.apps import apps
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import permiso_requerido
from .models import Categoria, Cliente, DetalleEncargo, Encargo, LogAuditoria, Producto, Rol, Usuario

PERMISO_AUDITORIA = 'ver_auditoria'
FILAS_POR_PAGINA = 30

NOMBRES_CAMPOS = {
    'nombre': 'Nombre',
    'apellido': 'Apellido',
    'descripcion': 'Descripción',
    'activo': 'Alta / baja',
    'nombre_permiso': 'Nombre del permiso',
    'nombre_rol': 'Nombre del rol',
    'email': 'Email',
    'calle': 'Calle',
    'numero': 'Número',
    'ciudad': 'Ciudad',
    'fecha_alta': 'Fecha de alta',
    'dni': 'DNI',
    'nombre_usuario': 'Nombre de usuario',
    'contrasena_hash': 'Contraseña',
    'debe_cambiar_clave': 'Debe cambiar la contraseña',
    'fecha_baja': 'Fecha de baja',
    'estado': 'Estado',
    'rol_id': 'Rol',
    'precio_unitario': 'Precio unitario',
    'stock_actual': 'Stock actual',
    'stock_minimo': 'Stock mínimo',
    'unidad': 'Unidad',
    'categoria_id': 'Categoría',
    'fecha_pedido': 'Fecha del pedido',
    'fecha_entrega_prevista': 'Fecha de entrega prevista',
    'senia': 'Seña',
    'total': 'Total',
    'medio_pago': 'Medio de pago de la seña',
    'observacion': 'Observación',
    'usuario_id': 'Registrado por',
    'cliente_id': 'Cliente',
    'fecha_entrega_real': 'Fecha de entrega',
    'fecha_anulacion': 'Fecha de cancelación',
    'motivo_anulacion': 'Motivo de cancelación',
    'usuario_anulacion_id': 'Cancelado por',
    'fecha_hora_registro': 'Fecha y hora de registro',
    'fecha_pago_saldo': 'Fecha de cobro del saldo',
    'medio_pago_saldo': 'Medio de cobro del saldo',
    'usuario_pago_saldo_id': 'Cobrado por',
    'producto_id': 'Producto',
    'encargo_id': 'Encargo',
    'cantidad': 'Cantidad',
    'subtotal': 'Subtotal',
    'preparado': 'Preparando',
    'porcentaje_devolucion': 'Porcentaje de devolución',
    'merma_porcentaje': 'Porcentaje de merma',
    'nota_credito': 'Nota de crédito',
    'monto_devuelto': 'Monto devuelto',
}

TEXTO_VACIO = {
    'fecha_pago_saldo': 'Pendiente',
    'medio_pago_saldo': 'Pendiente',
    'usuario_pago_saldo_id': 'Pendiente',
    'fecha_entrega_real': 'No entregado',
    'fecha_anulacion': 'No cancelado',
    'motivo_anulacion': 'No cancelado',
    'usuario_anulacion_id': 'No cancelado',
    'fecha_baja': 'Activo',
}

CAMPOS_RELACION = {
    'usuario_id': Usuario,
    'usuario_anulacion_id': Usuario,
    'usuario_pago_saldo_id': Usuario,
    'rol_id': Rol,
    'categoria_id': Categoria,
    'cliente_id': Cliente,
    'producto_id': Producto,
    'encargo_id': Encargo,
}


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


def _fecha_legible(valor):
    try:
        if len(valor) == 10:
            return datetime.strptime(valor, '%Y-%m-%d').strftime('%d/%m/%Y')
        momento = datetime.fromisoformat(valor.replace('Z', '+00:00'))
    except ValueError:
        return None
    if timezone.is_naive(momento):
        return momento.strftime('%d/%m/%Y %H:%M')
    return timezone.localtime(momento).strftime('%d/%m/%Y %H:%M')


def _texto_relacion(objeto):
    if isinstance(objeto, Usuario):
        return f'{objeto.nombre} {objeto.apellido}'
    if isinstance(objeto, Encargo):
        return objeto.numero_comprobante
    return str(objeto)


def _mostrar(campo, valor, relaciones):
    if valor is None or valor == '':
        return TEXTO_VACIO.get(campo, 'Sin dato')
    if campo in CAMPOS_RELACION:
        objeto = relaciones.get((CAMPOS_RELACION[campo], str(valor)))
        return _texto_relacion(objeto) if objeto is not None else valor
    if isinstance(valor, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}([T ][\d:.]+(Z|[+-]\d{2}:?\d{2})?)?', valor):
        legible = _fecha_legible(valor)
        if legible:
            return legible
    if isinstance(valor, bool):
        if campo == 'activo':
            return 'Dado de alta' if valor else 'Dado de baja'
        return 'Sí' if valor else 'No'
    return valor


def _relaciones(filas):
    ids_por_modelo = {}
    for fila in filas:
        for datos in (_leer(fila.valores_anteriores), _leer(fila.valores_actuales)):
            for campo, valor in datos.items():
                if campo in CAMPOS_RELACION and valor not in (None, ''):
                    ids_por_modelo.setdefault(CAMPOS_RELACION[campo], set()).add(valor)
    relaciones = {}
    for modelo, ids in ids_por_modelo.items():
        for pk, objeto in modelo.objects.in_bulk(list(ids)).items():
            relaciones[(modelo, str(pk))] = objeto
    return relaciones


def _cambios(log, relaciones):
    antes = _leer(log.valores_anteriores)
    despues = _leer(log.valores_actuales)
    campos = list(antes) + [c for c in despues if c not in antes]
    return [
        {
            'campo': NOMBRES_CAMPOS.get(c, c),
            'antes': _mostrar(c, antes[c], relaciones) if c in antes else '-',
            'despues': _mostrar(c, despues[c], relaciones) if c in despues else '-',
        }
        for c in campos
    ]


def _nombres_afectados(filas):
    modelos = {m._meta.db_table: m for m in apps.get_app_config('core').get_models()}
    ids_por_entidad = {}
    for fila in filas:
        ids_por_entidad.setdefault(fila.entidad, set()).add(fila.id_registro)
    nombres = {}
    for entidad, ids in ids_por_entidad.items():
        modelo = modelos.get(entidad)
        if modelo is None:
            continue
        consulta = modelo.objects.all()
        if modelo is Encargo:
            consulta = consulta.select_related('cliente')
        if modelo is DetalleEncargo:
            consulta = consulta.select_related('encargo', 'producto')
        for pk, objeto in consulta.in_bulk(list(ids)).items():
            if modelo is Encargo:
                nombres[(entidad, pk)] = f'{objeto.numero_comprobante} - {objeto.cliente}'
            else:
                nombres[(entidad, pk)] = str(objeto)
    for fila in filas:
        fila.afectado = nombres.get((fila.entidad, fila.id_registro), '-')


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

    pagina = Paginator(logs.order_by('-fecha_hora', '-id_log'), FILAS_POR_PAGINA).get_page(request.GET.get('page'))
    filas = list(pagina.object_list)
    relaciones = _relaciones(filas)
    for fila in filas:
        fila.cambios = _cambios(fila, relaciones)
    _nombres_afectados(filas)
    parametros = request.GET.copy()
    parametros.pop('page', None)

    return render(request, 'core/auditoria_lista.html', {
        'filas': filas,
        'pagina': pagina,
        'paginas': pagina.paginator.get_elided_page_range(pagina.number, on_each_side=2, on_ends=1),
        'parametros': parametros.urlencode(),
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
