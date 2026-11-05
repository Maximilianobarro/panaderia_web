from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import permiso_requerido
from .models import Cliente, DetalleVenta, Producto, Usuario, Venta

PERMISO_VER = 'ver_ventas'
PERMISO_REGISTRAR = 'registrar_venta'
PERMISO_COMPROBANTE = 'emitir_comprobante'

ESTADO_CONFIRMADA = 'Confirmada'
MEDIOS_PAGO = ['Efectivo', 'Transferencia', 'Tarjeta']
MAX_CANTIDAD = 100000
ZONA_LOCAL = dt_timezone(timedelta(hours=-3))
MESES = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]


def _hoy():
    return timezone.now().astimezone(ZONA_LOCAL).date()


def _resumen_mensual(valor_elegido):
    hoy = _hoy()
    actual = (hoy.year, hoy.month)
    filas = {actual: {'cantidad': 0, 'total': 0, 'medios': {}}}
    ventas = Venta.objects.filter(estado=ESTADO_CONFIRMADA).values_list('fecha_hora', 'total', 'medio_pago')
    for fecha, total, medio in ventas:
        local = fecha.astimezone(ZONA_LOCAL)
        fila = filas.setdefault((local.year, local.month), {'cantidad': 0, 'total': 0, 'medios': {}})
        fila['cantidad'] += 1
        fila['total'] += total
        fila['medios'][medio] = fila['medios'].get(medio, 0) + total
    claves = sorted(filas, reverse=True)
    try:
        pedido = datetime.strptime(valor_elegido, '%Y-%m')
        elegido = (pedido.year, pedido.month)
    except (TypeError, ValueError):
        elegido = actual
    if elegido not in filas:
        elegido = actual
    opciones = [
        {'valor': f'{a}-{m:02d}', 'texto': f'{MESES[m - 1]} de {a}'}
        for a, m in claves
    ]
    anio, mes = elegido
    fila = filas[elegido]
    inicio = date(anio, mes, 1)
    siguiente = date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    resumen = {
        'valor': f'{anio}-{mes:02d}',
        'desde': inicio.isoformat(),
        'hasta': (siguiente - timedelta(days=1)).isoformat(),
        'cantidad': fila['cantidad'],
        'total': fila['total'],
        'promedio': (fila['total'] / fila['cantidad']) if fila['cantidad'] else 0,
        'medios': [fila['medios'].get(m, 0) for m in MEDIOS_PAGO],
    }
    return opciones, resumen


def _usuario_actual(request):
    return Usuario.objects.get(pk=request.session['usuario_id'])


def _parse_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _inicio_dia(fecha):
    return datetime.combine(fecha, time.min, tzinfo=ZONA_LOCAL)


def _leer_items(ids, cantidades, errores):
    items = {}
    for pid, cant in zip(ids, cantidades):
        pid = pid.strip()
        cant = cant.strip()
        if not pid and not cant:
            continue
        if not pid.isdecimal():
            errores.append('Elegí un producto de la lista en cada fila.')
            continue
        if not cant.isdecimal() or not (1 <= int(cant) <= MAX_CANTIDAD):
            errores.append(f'La cantidad debe ser un número entero entre 1 y {MAX_CANTIDAD}.')
            continue
        items[int(pid)] = items.get(int(pid), 0) + int(cant)
    return items


def _registrar_venta(request, cliente_id, medio_pago, ids, cantidades, errores):
    cliente = None
    if cliente_id.isdecimal():
        cliente = Cliente.objects.filter(pk=int(cliente_id), activo=True).first()
    if cliente is None:
        errores.append('Elegí un cliente de la lista.')

    if medio_pago not in MEDIOS_PAGO:
        errores.append('Elegí un medio de pago de la lista.')

    items = _leer_items(ids, cantidades, errores)
    if not items:
        errores.append('Agregá al menos un producto a la venta.')

    if errores:
        return None

    with transaction.atomic():
        productos = {
            p.pk: p
            for p in Producto.objects.select_for_update()
            .filter(pk__in=list(items))
            .order_by('pk')
        }

        for pid, cant in items.items():
            producto = productos.get(pid)
            if producto is None:
                errores.append('Hay un producto que ya no existe.')
            elif (producto.estado or '').lower() != 'activo':
                errores.append(f'«{producto.nombre}» está inactivo y no se puede vender.')
            elif (producto.stock_actual or 0) < cant:
                errores.append(
                    f'Stock insuficiente de «{producto.nombre}»: '
                    f'disponible {producto.stock_actual or 0}, pedido {cant}.'
                )

        if errores:
            return None

        venta = Venta.objects.create(
            fecha_hora=timezone.now(),
            medio_pago=medio_pago,
            estado=ESTADO_CONFIRMADA,
            usuario=_usuario_actual(request),
            cliente=cliente,
            total=Decimal('0'),
        )

        total = Decimal('0')
        for pid in sorted(items):
            producto = productos[pid]
            cant = items[pid]
            subtotal = producto.precio_unitario * cant
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cant,
                precio_unitario_venta=producto.precio_unitario,
                subtotal=subtotal,
            )
            producto.stock_actual = (producto.stock_actual or 0) - cant
            producto.save(update_fields=['stock_actual'])
            total += subtotal

        venta.total = total
        venta.save(update_fields=['total'])

    return venta


@permiso_requerido(PERMISO_REGISTRAR)
@require_http_methods(['GET', 'POST'])
def venta_crear(request):
    errores = []
    cliente_id = ''
    medio_pago = ''
    lineas = []

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente', '').strip()
        medio_pago = request.POST.get('medio_pago', '').strip()
        ids = request.POST.getlist('producto')
        cantidades = request.POST.getlist('cantidad')
        lineas = [{'producto': p, 'cantidad': c} for p, c in zip(ids, cantidades)]

        venta = _registrar_venta(request, cliente_id, medio_pago, ids, cantidades, errores)
        if venta is not None:
            messages.success(
                request,
                f'Venta {venta.numero_comprobante} registrada. El stock fue actualizado.'
            )
            return redirect('venta_detalle', pk=venta.pk)

    if request.method == 'GET':
        generico = Cliente.objects.filter(
            nombre__iexact='Consumidor', apellido__iexact='Final'
        ).first()
        if generico:
            cliente_id = str(generico.pk)

    productos = (
        Producto.objects.filter(estado__iexact='activo')
        .select_related('categoria')
        .order_by('nombre')
    )
    productos_json = [
        {
            'id': p.pk,
            'nombre': p.nombre,
            'precio': str(p.precio_unitario),
            'stock': p.stock_actual or 0,
            'categoria': p.categoria.nombre,
        }
        for p in productos
    ]

    return render(request, 'core/venta_form.html', {
        'clientes': Cliente.objects.filter(activo=True).order_by('apellido', 'nombre'),
        'productos_json': productos_json,
        'medios_pago': MEDIOS_PAGO,
        'errores': list(dict.fromkeys(errores)),
        'cliente_id': cliente_id,
        'medio_pago': medio_pago,
        'lineas': lineas,
    })


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def venta_lista(request):
    errores = []
    desde_txt = request.GET.get('desde', '').strip()
    hasta_txt = request.GET.get('hasta', '').strip()
    cliente_id = request.GET.get('cliente', '').strip()
    producto_id = request.GET.get('producto', '').strip()
    mes_txt = request.GET.get('mes', '').strip()
    opciones_mes, resumen_mes = _resumen_mensual(mes_txt)
    if mes_txt and not desde_txt and not hasta_txt:
        if resumen_mes['valor'] == mes_txt:
            desde_txt = resumen_mes['desde']
            hasta_txt = resumen_mes['hasta']

    desde = _parse_fecha(desde_txt) if desde_txt else None
    hasta = _parse_fecha(hasta_txt) if hasta_txt else None
    if desde_txt and desde is None:
        errores.append('La fecha "desde" no es válida.')
    if hasta_txt and hasta is None:
        errores.append('La fecha "hasta" no es válida.')
    if desde and hasta and desde > hasta:
        errores.append('La fecha "desde" no puede ser posterior a "hasta".')
        desde = hasta = None

    ventas = Venta.objects.all()
    if desde:
        ventas = ventas.filter(fecha_hora__gte=_inicio_dia(desde))
    if hasta:
        ventas = ventas.filter(fecha_hora__lt=_inicio_dia(hasta + timedelta(days=1)))
    if cliente_id.isdecimal():
        ventas = ventas.filter(cliente_id=int(cliente_id))
    if producto_id.isdecimal():
        ventas = ventas.filter(
            id_venta__in=DetalleVenta.objects.filter(
                producto_id=int(producto_id)
            ).values('venta_id')
        )

    ventas = list(
        ventas.select_related('cliente', 'usuario').order_by('-fecha_hora', '-id_venta')
    )

    return render(request, 'core/venta_lista.html', {
        'ventas': ventas,
        'opciones_mes': opciones_mes,
        'resumen_mes': resumen_mes,
        'medios_pago': MEDIOS_PAGO,
        'errores': errores,
        'clientes': Cliente.objects.order_by('apellido', 'nombre'),
        'productos': Producto.objects.order_by('nombre'),
        'filtros': {
            'desde': desde_txt,
            'hasta': hasta_txt,
            'cliente': cliente_id,
            'producto': producto_id,
        },
    })


def _datos_venta(pk):
    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'usuario'),
        pk=pk,
    )
    detalles = (
        DetalleVenta.objects.filter(venta=venta)
        .select_related('producto')
        .order_by('id')
    )
    return venta, detalles


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def venta_detalle(request, pk):
    venta, detalles = _datos_venta(pk)
    return render(request, 'core/venta_detalle.html', {
        'venta': venta,
        'detalles': detalles,
    })


@permiso_requerido(PERMISO_COMPROBANTE)
@require_http_methods(['GET'])
def venta_comprobante(request, pk):
    venta, detalles = _datos_venta(pk)
    return render(request, 'core/venta_comprobante.html', {
        'venta': venta,
        'detalles': detalles,
    })
