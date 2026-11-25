
import base64
import hashlib
import threading
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Count, DecimalField, F, Max, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import permiso_requerido
from .models import (
    Categoria, CierreCaja, Cliente, DetalleEncargo, DetalleVenta, Encargo, NotaCredito, Usuario, Venta,
)
from .reportes_pdf import generar_pdf, generar_pdf_graficos, generar_pdf_imagen
from .views_hito3 import ESTADO_CONFIRMADA, ZONA_LOCAL, _hoy, _inicio_dia, _parse_fecha, _usuario_actual

PERMISO_REPORTES = 'ver_reportes'
PERMISO_REPORTE_EMPLEADOS = 'ver_reporte_empleados'
FILAS_POR_PAGINA = 30
CERO = Decimal('0')
MONEDA = DecimalField(max_digits=14, decimal_places=2)


# ---------- Formato ----------

def _moneda(valor):
    return f'${valor:,.2f}'


def _porcentaje(parte, total):
    return f'{(parte * 100 / total):.1f}%' if total else '0.0%'


def _fecha_txt(fecha):
    return fecha.strftime('%d/%m/%Y')


def _cantidad(n, singular, plural):
    return f'{n} {singular if n == 1 else plural}'


# ---------- Filtros comunes ----------

def _leer_rango(request, errores, dias_defecto=None):
    """Lee Desde/Hasta (aaaa-mm-dd). Sin fechas, usa el mes en curso (o los últimos `dias_defecto` días)."""
    desde_txt = request.GET.get('desde', '').strip()
    hasta_txt = request.GET.get('hasta', '').strip()
    hoy = _hoy()
    inicio_defecto = hoy - timedelta(days=dias_defecto - 1) if dias_defecto else hoy.replace(day=1)
    desde = _parse_fecha(desde_txt) if desde_txt else inicio_defecto
    hasta = _parse_fecha(hasta_txt) if hasta_txt else hoy
    if desde is None:
        errores.append('La fecha "desde" no es válida.')
        desde = inicio_defecto
    if hasta is None:
        errores.append('La fecha "hasta" no es válida.')
        hasta = hoy
    if desde > hasta:
        errores.append('La fecha "desde" no puede ser posterior a "hasta". Se muestra el período por defecto.')
        desde, hasta = inicio_defecto, hoy
    return desde, hasta


def _limites(desde, hasta):
    """Convierte el rango de días (hora Argentina) en límites [inicio, fin)."""
    return _inicio_dia(desde), _inicio_dia(hasta + timedelta(days=1))


def _en_rango(campo, inicio, fin):
    return {f'{campo}__gte': inicio, f'{campo}__lt': fin}


# ---------- Reporte 1: Ventas por producto ----------

def _datos_productos(desde, hasta, categoria_id):
    inicio, fin = _limites(desde, hasta)
    ventas = DetalleVenta.objects.filter(
        venta__estado=ESTADO_CONFIRMADA, **_en_rango('venta__fecha_hora', inicio, fin),
    )
    encargos = DetalleEncargo.objects.filter(
        encargo__estado=Encargo.ESTADO_ENTREGADO, **_en_rango('encargo__fecha_entrega_real', inicio, fin),
    )
    if categoria_id:
        ventas = ventas.filter(producto__categoria_id=categoria_id)
        encargos = encargos.filter(producto__categoria_id=categoria_id)

    filas = {}

    def fila(pid, nombre, categoria):
        return filas.setdefault(pid, {
            'producto': nombre, 'categoria': categoria,
            'u_ventas': 0, 'i_ventas': CERO, 'u_encargos': 0, 'i_encargos': CERO,
        })

    campos = ('producto_id', 'producto__nombre', 'producto__categoria__nombre')
    for r in ventas.values(*campos).annotate(unidades=Sum('cantidad'), importe=Sum('subtotal')):
        f = fila(r['producto_id'], r['producto__nombre'], r['producto__categoria__nombre'])
        f['u_ventas'] = r['unidades'] or 0
        f['i_ventas'] = r['importe'] or CERO
    for r in encargos.values(*campos).annotate(unidades=Sum('cantidad'), importe=Sum('subtotal')):
        f = fila(r['producto_id'], r['producto__nombre'], r['producto__categoria__nombre'])
        f['u_encargos'] = r['unidades'] or 0
        f['i_encargos'] = r['importe'] or CERO

    datos = list(filas.values())
    for f in datos:
        f['u_total'] = f['u_ventas'] + f['u_encargos']
        f['i_total'] = f['i_ventas'] + f['i_encargos']
    datos.sort(key=lambda f: (-f['i_total'], f['producto']))
    gran_total = sum((f['i_total'] for f in datos), CERO)

    columnas = [
        ('Producto', 'izq'), ('Categoría', 'izq'), ('Unid. mostrador', 'der'), ('$ mostrador', 'der'),
        ('Unid. encargos', 'der'), ('$ encargos', 'der'), ('Unid. total', 'der'), ('$ total', 'der'),
        ('% del total', 'der'),
    ]
    filas_txt = [[
        f['producto'], f['categoria'], f['u_ventas'], _moneda(f['i_ventas']), f['u_encargos'],
        _moneda(f['i_encargos']), f['u_total'], _moneda(f['i_total']), _porcentaje(f['i_total'], gran_total),
    ] for f in datos]
    totales = [
        'TOTAL', _cantidad(len(datos), 'producto', 'productos'),
        sum(f['u_ventas'] for f in datos), _moneda(sum((f['i_ventas'] for f in datos), CERO)),
        sum(f['u_encargos'] for f in datos), _moneda(sum((f['i_encargos'] for f in datos), CERO)),
        sum(f['u_total'] for f in datos), _moneda(gran_total), '100.0%' if datos else '0.0%',
    ]
    return columnas, filas_txt, totales


# ---------- Reporte 2: Ranking de clientes ----------

ESTADOS_CLIENTE = [('', 'Todos'), ('activos', 'Activos'), ('baja', 'Dados de baja')]


def _es_consumidor_final(cliente):
    return (cliente.nombre or '').strip().lower() == 'consumidor' and (cliente.apellido or '').strip().lower() == 'final'


def _datos_clientes(desde, hasta, estado, incluir_cf):
    inicio, fin = _limites(desde, hasta)
    consulta = Cliente.objects.all()
    if estado == 'activos':
        consulta = consulta.filter(activo=True)
    elif estado == 'baja':
        consulta = consulta.filter(activo=False)
    clientes = {c.pk: c for c in consulta if incluir_cf or not _es_consumidor_final(c)}
    ids = list(clientes)

    filas = {pk: {
        'cliente': str(c), 'n_ventas': 0, 'i_ventas': CERO, 'n_entregados': 0, 'i_entregados': CERO,
        'n_cancelados': 0, 'devuelto': CERO,
    } for pk, c in clientes.items()}

    for r in Venta.objects.filter(
        estado=ESTADO_CONFIRMADA, cliente_id__in=ids, **_en_rango('fecha_hora', inicio, fin),
    ).values('cliente_id').annotate(n=Count('pk'), i=Sum('total')):
        filas[r['cliente_id']]['n_ventas'] = r['n']
        filas[r['cliente_id']]['i_ventas'] = r['i'] or CERO
    for r in Encargo.objects.filter(
        estado=Encargo.ESTADO_ENTREGADO, cliente_id__in=ids, **_en_rango('fecha_entrega_real', inicio, fin),
    ).values('cliente_id').annotate(n=Count('pk'), i=Sum('total')):
        filas[r['cliente_id']]['n_entregados'] = r['n']
        filas[r['cliente_id']]['i_entregados'] = r['i'] or CERO
    for r in Encargo.objects.filter(
        estado=Encargo.ESTADO_CANCELADO, cliente_id__in=ids, **_en_rango('fecha_anulacion', inicio, fin),
    ).values('cliente_id').annotate(n=Count('pk')):
        filas[r['cliente_id']]['n_cancelados'] = r['n']
    for r in NotaCredito.objects.filter(
        encargo__cliente_id__in=ids, **_en_rango('fecha_hora', inicio, fin),
    ).values('encargo__cliente_id').annotate(i=Sum('monto')):
        filas[r['encargo__cliente_id']]['devuelto'] = r['i'] or CERO

    datos = [f for f in filas.values() if f['n_ventas'] or f['n_entregados'] or f['n_cancelados'] or f['devuelto']]
    for f in datos:
        f['total'] = f['i_ventas'] + f['i_entregados']
    datos.sort(key=lambda f: (-f['total'], f['cliente']))
    gran_total = sum((f['total'] for f in datos), CERO)

    columnas = [
        ('Puesto', 'der'), ('Cliente', 'izq'), ('Ventas', 'der'), ('$ ventas', 'der'),
        ('Encargos entregados', 'der'), ('$ encargos', 'der'), ('Encargos cancelados', 'der'),
        ('$ devuelto (NC)', 'der'), ('$ total facturado', 'der'), ('% del total', 'der'),
    ]
    filas_txt = [[
        i, f['cliente'], f['n_ventas'], _moneda(f['i_ventas']), f['n_entregados'], _moneda(f['i_entregados']),
        f['n_cancelados'], _moneda(f['devuelto']), _moneda(f['total']), _porcentaje(f['total'], gran_total),
    ] for i, f in enumerate(datos, start=1)]
    totales = [
        '', f"TOTAL ({_cantidad(len(datos), 'cliente', 'clientes')})",
        sum(f['n_ventas'] for f in datos), _moneda(sum((f['i_ventas'] for f in datos), CERO)),
        sum(f['n_entregados'] for f in datos), _moneda(sum((f['i_entregados'] for f in datos), CERO)),
        sum(f['n_cancelados'] for f in datos), _moneda(sum((f['devuelto'] for f in datos), CERO)),
        _moneda(gran_total), '100.0%' if datos else '0.0%',
    ]
    return columnas, filas_txt, totales


# ---------- Reporte 3: Rendición por empleado ----------

def _sumar_por(consulta, campo_usuario, expresion, medio=None, campo_medio=None):
    """Suma `expresion` agrupando por usuario (y, si se indica, solo un medio de pago)."""
    if medio is not None:
        consulta = consulta.filter(**{campo_medio: medio})
    filas = consulta.values(campo_usuario).annotate(
        i=Coalesce(Sum(expresion, output_field=MONEDA), Value(CERO), output_field=MONEDA),
    )
    return {r[campo_usuario]: r['i'] or CERO for r in filas}


def _datos_empleados(desde, hasta, usuario_id):
    inicio, fin = _limites(desde, hasta)
    usuarios = Usuario.objects.order_by('nombre_usuario')
    if usuario_id:
        usuarios = usuarios.filter(pk=usuario_id)
    usuarios = list(usuarios)
    ids = [u.pk for u in usuarios]

    ventas = Venta.objects.filter(estado=ESTADO_CONFIRMADA, usuario_id__in=ids, **_en_rango('fecha_hora', inicio, fin))
    senias = Encargo.objects.filter(usuario_id__in=ids, senia__gt=0, **_en_rango('fecha_hora_registro', inicio, fin))
    saldos = Encargo.objects.filter(usuario_pago_saldo_id__in=ids, **_en_rango('fecha_pago_saldo', inicio, fin))
    notas = NotaCredito.objects.filter(usuario_id__in=ids, **_en_rango('fecha_hora', inicio, fin))
    saldo = F('total') - Coalesce(F('senia'), Value(CERO), output_field=MONEDA)

    n_ventas = {r['usuario_id']: r['n'] for r in ventas.values('usuario_id').annotate(n=Count('pk'))}
    i_ventas = _sumar_por(ventas, 'usuario_id', 'total')
    i_senias = _sumar_por(senias, 'usuario_id', 'senia')
    i_saldos = _sumar_por(saldos, 'usuario_pago_saldo_id', saldo)
    i_notas = _sumar_por(notas, 'usuario_id', 'monto')
    e_ventas = _sumar_por(ventas, 'usuario_id', 'total', 'Efectivo', 'medio_pago')
    e_senias = _sumar_por(senias, 'usuario_id', 'senia', 'Efectivo', 'medio_pago')
    e_saldos = _sumar_por(saldos, 'usuario_pago_saldo_id', saldo, 'Efectivo', 'medio_pago_saldo')
    e_notas = _sumar_por(notas, 'usuario_id', 'monto', 'Efectivo', 'medio_devolucion')
    cajas = {
        r['usuario_id']: r['n']
        for r in CierreCaja.objects.filter(
            usuario_id__in=ids, estado=CierreCaja.ESTADO_CERRADA, **_en_rango('hasta', inicio, fin),
        ).values('usuario_id').annotate(n=Count('pk'))
    }

    datos = []
    for u in usuarios:
        f = {
            'empleado': f'{u.nombre} {u.apellido} ({u.nombre_usuario})',
            'n_ventas': n_ventas.get(u.pk, 0),
            'ventas': i_ventas.get(u.pk, CERO),
            'senias': i_senias.get(u.pk, CERO),
            'saldos': i_saldos.get(u.pk, CERO),
            'notas': i_notas.get(u.pk, CERO),
            'efectivo': (e_ventas.get(u.pk, CERO) + e_senias.get(u.pk, CERO)
                         + e_saldos.get(u.pk, CERO) - e_notas.get(u.pk, CERO)),
            'cajas': cajas.get(u.pk, 0),
        }
        f['neto'] = f['ventas'] + f['senias'] + f['saldos'] - f['notas']
        if f['n_ventas'] or f['senias'] or f['saldos'] or f['notas'] or f['cajas']:
            datos.append(f)
    datos.sort(key=lambda f: (-f['neto'], f['empleado']))

    columnas = [
        ('Empleado', 'izq'), ('Ventas', 'der'), ('$ ventas', 'der'), ('$ señas cobradas', 'der'),
        ('$ saldos cobrados', 'der'), ('$ devoluciones (NC)', 'der'), ('$ neto cobrado', 'der'),
        ('$ efectivo neto', 'der'), ('Cajas cerradas', 'der'),
    ]
    filas_txt = [[
        f['empleado'], f['n_ventas'], _moneda(f['ventas']), _moneda(f['senias']), _moneda(f['saldos']),
        _moneda(f['notas']), _moneda(f['neto']), _moneda(f['efectivo']), f['cajas'],
    ] for f in datos]

    def suma(clave):
        return sum((f[clave] for f in datos), CERO)

    totales = [
        f"TOTAL ({_cantidad(len(datos), 'empleado', 'empleados')})", sum(f['n_ventas'] for f in datos), _moneda(suma('ventas')),
        _moneda(suma('senias')), _moneda(suma('saldos')), _moneda(suma('notas')), _moneda(suma('neto')),
        _moneda(suma('efectivo')), sum(f['cajas'] for f in datos),
    ]
    return columnas, filas_txt, totales


# ---------- Armado común: pantalla o PDF ----------

def _responder(request, reporte, desde, hasta, filtros_txt, filtro_extra, columnas, filas, totales, errores):
    filtros_pie = [('Desde', _fecha_txt(desde)), ('Hasta', _fecha_txt(hasta))] + filtros_txt
    if request.GET.get('formato') == 'pdf':
        usuario = _usuario_actual(request)
        contenido = generar_pdf(
            titulo=reporte['titulo'],
            descripcion=reporte['descripcion'],
            columnas=columnas,
            filas=filas,
            totales=totales,
            filtros=filtros_pie,
            usuario=f'{usuario.nombre} {usuario.apellido} ({usuario.nombre_usuario})',
            generado=timezone.now().astimezone(ZONA_LOCAL),
        )
        respuesta = HttpResponse(contenido, content_type='application/pdf')
        respuesta['Content-Disposition'] = (
            f'attachment; filename="{reporte["archivo"]}_{desde:%Y%m%d}_{hasta:%Y%m%d}.pdf"'
        )
        return respuesta

    pagina = Paginator(filas, FILAS_POR_PAGINA).get_page(request.GET.get('page'))
    parametros = request.GET.copy()
    parametros.pop('page', None)
    parametros.pop('formato', None)
    return render(request, 'core/reporte.html', {
        'reporte': reporte,
        'columnas': columnas,
        'columnas_derecha': [i for i, (_, alineacion) in enumerate(columnas) if alineacion == 'der'],
        'pagina': pagina,
        'paginas': pagina.paginator.get_elided_page_range(pagina.number, on_each_side=2, on_ends=1),
        'totales': totales,
        'errores': errores,
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'filtro_extra': filtro_extra,
        'filtros_pie': filtros_pie,
        'parametros': parametros.urlencode(),
    })


def _id_elegido(texto, opciones):
    return int(texto) if texto.isdecimal() and int(texto) in opciones else None


@permiso_requerido(PERMISO_REPORTES)
@require_http_methods(['GET'])
def reporte_productos(request):
    errores = []
    desde, hasta = _leer_rango(request, errores)
    categorias = {c.pk: c.nombre for c in Categoria.objects.order_by('nombre')}
    categoria_id = _id_elegido(request.GET.get('categoria', '').strip(), categorias)
    columnas, filas, totales = _datos_productos(desde, hasta, categoria_id)
    filtro_extra = [{
        'tipo': 'select', 'nombre': 'categoria', 'etiqueta': 'Categoría',
        'opciones': [('', 'Todas')] + [(str(pk), nombre) for pk, nombre in categorias.items()],
        'valor': str(categoria_id) if categoria_id else '',
    }]
    reporte = {
        'titulo': 'Ventas por producto',
        'descripcion': 'Unidades e importes de cada producto: ventas de mostrador confirmadas (por fecha de venta) '
                       'más encargos entregados (por fecha de entrega).',
        'archivo': 'ventas_por_producto',
        'url': 'reporte_productos',
    }
    filtros_txt = [('Categoría', categorias.get(categoria_id, 'Todas'))]
    return _responder(request, reporte, desde, hasta, filtros_txt, filtro_extra, columnas, filas, totales, errores)


@permiso_requerido(PERMISO_REPORTES)
@require_http_methods(['GET'])
def reporte_clientes(request):
    errores = []
    desde, hasta = _leer_rango(request, errores)
    estado = request.GET.get('estado', '').strip()
    if estado not in dict(ESTADOS_CLIENTE):
        estado = ''
    incluir_cf = request.GET.get('incluir_cf') == '1'
    columnas, filas, totales = _datos_clientes(desde, hasta, estado, incluir_cf)
    filtro_extra = [
        {'tipo': 'select', 'nombre': 'estado', 'etiqueta': 'Estado del cliente',
         'opciones': ESTADOS_CLIENTE, 'valor': estado},
        {'tipo': 'check', 'nombre': 'incluir_cf', 'etiqueta': 'Incluir «Consumidor Final»', 'valor': incluir_cf},
    ]
    reporte = {
        'titulo': 'Ranking de clientes',
        'descripcion': 'Clientes ordenados por lo facturado (ventas confirmadas más encargos entregados), con los '
                       'encargos cancelados y lo devuelto con notas de crédito en el período.',
        'archivo': 'ranking_clientes',
        'url': 'reporte_clientes',
    }
    filtros_txt = [
        ('Estado del cliente', dict(ESTADOS_CLIENTE)[estado]),
        ('Consumidor Final', 'Incluido' if incluir_cf else 'Excluido'),
    ]
    return _responder(request, reporte, desde, hasta, filtros_txt, filtro_extra, columnas, filas, totales, errores)


@permiso_requerido(PERMISO_REPORTE_EMPLEADOS)
@require_http_methods(['GET'])
def reporte_empleados(request):
    errores = []
    desde, hasta = _leer_rango(request, errores)
    usuarios = {
        u.pk: f'{u.nombre} {u.apellido} ({u.nombre_usuario})'
        for u in Usuario.objects.order_by('nombre_usuario')
    }
    usuario_id = _id_elegido(request.GET.get('empleado', '').strip(), usuarios)
    columnas, filas, totales = _datos_empleados(desde, hasta, usuario_id)
    filtro_extra = [{
        'tipo': 'select', 'nombre': 'empleado', 'etiqueta': 'Empleado',
        'opciones': [('', 'Todos')] + [(str(pk), nombre) for pk, nombre in usuarios.items()],
        'valor': str(usuario_id) if usuario_id else '',
    }]
    reporte = {
        'titulo': 'Rendición por empleado',
        'descripcion': 'Dinero que manejó cada empleado: ventas, señas y saldos de encargos cobrados, menos las '
                       'devoluciones con notas de crédito, y las cajas que cerró. Reporte restringido.',
        'archivo': 'rendicion_por_empleado',
        'url': 'reporte_empleados',
    }
    filtros_txt = [('Empleado', usuarios.get(usuario_id, 'Todos'))]
    return _responder(request, reporte, desde, hasta, filtros_txt, filtro_extra, columnas, filas, totales, errores)


# ---------- Página de Reportes: análisis con gráficos (mismo código que el módulo de analítica) ----------

DIAS_GRAFICOS = 90
# matplotlib no es seguro para dibujar desde varios pedidos a la vez: se dibuja de a uno.
_BLOQUEO_GRAFICOS = threading.Lock()
# Los gráficos de la pantalla se guardan en la caché de Django (en memoria) para no redibujarlos en cada visita.
# La clave incluye los filtros y una "versión" de los datos: si se registra una venta o se entrega
# un encargo, la versión cambia y los gráficos se vuelven a dibujar.
SEGUNDOS_CACHE = 30 * 60


def _plata(valor):
    return _moneda(Decimal(str(round(valor, 2))))


def _indicadores(datos):
    """Indicadores para la pantalla y el PDF: (nombre, valor, detalle)."""
    principales = [
        ('Facturación total', _plata(datos['facturacion']), 'Ventas de mostrador + encargos entregados'),
        ('Operaciones analizadas', f'{datos["operaciones"]:,}',
         f'{datos["ventas"]:,} ventas y {datos["encargos"]:,} encargos'),
        ('Ticket promedio', _plata(datos['ticket_promedio']), 'Promedio por venta de mostrador'),
        ('Producto líder', datos['producto_lider'], f'{datos["producto_lider_pct"]:.1f}% de la facturación'),
    ]
    estadisticos = [
        ('Mediana del ticket', _plata(datos['ticket_mediana']), 'La mitad de las ventas es menor a este monto'),
        ('Percentil 90 del ticket', _plata(datos['ticket_p90']), 'El 90% de las ventas es menor a este monto'),
        ('Desviación estándar', _plata(datos['ticket_desvio']), 'Cuánto varían los montos de las ventas'),
        ('Ventas inusuales', f'{datos["ventas_inusuales"]:,}', f'Mayores a {_plata(datos["limite_inusual"])} '
                                                               '(promedio + 3 desvíos)'),
    ]
    return principales, estadisticos


def _version_datos():
    """Cambia cada vez que se registra una venta o un encargo, o se entrega o cancela un encargo."""
    ventas = Venta.objects.aggregate(ultima=Max('id_venta'), cantidad=Count('id_venta'))
    encargos = Encargo.objects.aggregate(
        ultimo=Max('id_encargo'), entrega=Max('fecha_entrega_real'), anulacion=Max('fecha_anulacion'),
        entregados=Count('id_encargo', filter=Q(estado=Encargo.ESTADO_ENTREGADO)),
    )
    return f'{ventas}|{encargos}'


def _filtros_analisis(request):
    """Lee los filtros del análisis (fechas y categoría), comunes a la pantalla y al tablero."""
    errores = []
    desde, hasta = _leer_rango(request, errores, dias_defecto=DIAS_GRAFICOS)
    categorias = list(Categoria.objects.order_by('nombre').values_list('nombre', flat=True))
    categoria = request.GET.get('categoria', '').strip()
    if categoria not in categorias:
        categoria = ''
    filtros_pie = [('Desde', _fecha_txt(desde)), ('Hasta', _fecha_txt(hasta)), ('Categoría', categoria or 'Todas')]
    return errores, desde, hasta, categoria, categorias, filtros_pie


def _motor_y_datos(desde, hasta, categoria, errores):
    """Importa el módulo de analítica y lee los datos. Devuelve (motor, lineas, operaciones) o None."""
    try:
        from analitica import analitica as motor
    except ImportError:
        errores.append('Faltan las librerías de gráficos (pandas, numpy, matplotlib). '
                       'Corré: pip install -r requirements.txt')
        return None
    lineas, operaciones = motor.leer_datos(connection, desde, hasta)
    if categoria and not lineas.empty:
        lineas = lineas[lineas['categoria'] == categoria]
    if lineas.empty:
        errores.append('No hay ventas ni encargos entregados para los filtros elegidos.')
        return None
    return motor, lineas, operaciones


def _usuario_texto(request):
    usuario = _usuario_actual(request)
    return f'{usuario.nombre} {usuario.apellido} ({usuario.nombre_usuario})'


def _respuesta_pdf(contenido, nombre):
    respuesta = HttpResponse(contenido, content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


@permiso_requerido(PERMISO_REPORTES)
@require_http_methods(['GET'])
def reporte_index(request):
    errores, desde, hasta, categoria, categorias, filtros_pie = _filtros_analisis(request)
    parametros = request.GET.copy()
    parametros.pop('formato', None)
    contexto = {
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'categorias': categorias,
        'categoria': categoria,
        'filtros_pie': filtros_pie,
        'errores': errores,
        'parametros': parametros.urlencode(),
    }
    es_pdf = request.GET.get('formato') == 'pdf'

    clave = 'analisis-' + hashlib.md5(f'{desde}|{hasta}|{categoria}|{_version_datos()}'.encode()).hexdigest()
    analisis = None if es_pdf else cache.get(clave)
    if analisis is None:
        resultado = _motor_y_datos(desde, hasta, categoria, errores)
        if resultado is None:
            return render(request, 'core/reporte_index.html', contexto)
        motor, lineas, operaciones = resultado
        principales, estadisticos = _indicadores(motor.indicadores(lineas, desde, hasta))
        with _BLOQUEO_GRAFICOS:
            graficos = motor.crear_figuras(lineas, operaciones, desde, hasta, categoria=categoria or None,
                                           incluir_tablero=False)
            for g in graficos:
                g['png'] = motor.figura_png(g.pop('figura'), dpi=150 if es_pdf else 110)

        if es_pdf:
            contenido = generar_pdf_graficos(
                titulo='Análisis de ventas',
                descripcion='Ventas de mostrador confirmadas y encargos entregados del período. Cada gráfico '
                            'responde la pregunta de negocio indicada debajo de su título.',
                indicadores=[(n, v) for n, v, _ in principales + estadisticos],
                imagenes=[(g['titulo'], g['png']) for g in graficos],
                filtros=filtros_pie,
                usuario=_usuario_texto(request),
                generado=timezone.now().astimezone(ZONA_LOCAL),
            )
            return _respuesta_pdf(contenido, f'analisis_ventas_{desde:%Y%m%d}_{hasta:%Y%m%d}.pdf')

        for g in graficos:
            g['imagen'] = 'data:image/png;base64,' + base64.b64encode(g.pop('png')).decode()
        analisis = {'principales': principales, 'estadisticos': estadisticos, 'graficos': graficos}
        cache.set(clave, analisis, SEGUNDOS_CACHE)

    contexto.update(analisis)
    return render(request, 'core/reporte_index.html', contexto)


@permiso_requerido(PERMISO_REPORTES)
@require_http_methods(['GET'])
def reporte_tablero(request):
    """Tablero ejecutivo imprimible: los indicadores y los cuatro gráficos en una sola página PDF."""
    errores, desde, hasta, categoria, _, filtros_pie = _filtros_analisis(request)
    resultado = _motor_y_datos(desde, hasta, categoria, errores)
    if resultado is None:
        for error in errores:
            messages.error(request, error)
        return redirect('reporte_index')
    motor, lineas, operaciones = resultado
    with _BLOQUEO_GRAFICOS:
        figura = motor.crear_tablero(lineas, operaciones, desde, hasta, 6,
                                     motor.subtitulo_periodo(desde, hasta, categoria or None))
        png = motor.figura_png(figura, dpi=170)
    contenido = generar_pdf_imagen(
        titulo='Tablero ejecutivo',
        png=png,
        filtros=filtros_pie,
        usuario=_usuario_texto(request),
        generado=timezone.now().astimezone(ZONA_LOCAL),
    )
    return _respuesta_pdf(contenido, f'tablero_ejecutivo_{desde:%Y%m%d}_{hasta:%Y%m%d}.pdf')
