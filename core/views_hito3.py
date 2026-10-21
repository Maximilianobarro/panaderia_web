from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import permiso_requerido
from .models import Cliente, DetalleVenta, Producto, Usuario, Venta

PERMISO_VER = 'ver_ventas'
PERMISO_REGISTRAR = 'registrar_venta'
PERMISO_ANULAR = 'anular_venta'
PERMISO_COMPROBANTE = 'emitir_comprobante'

ESTADO_CONFIRMADA = 'Confirmada'
ESTADO_ANULADA = 'Anulada'
MEDIOS_PAGO = ['Efectivo', 'Transferencia', 'Tarjeta']
MAX_CANTIDAD = 100000


def _usuario_actual(request):
    return Usuario.objects.get(pk=request.session['usuario_id'])


def _parse_fecha(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _inicio_dia(fecha):
    return timezone.make_aware(datetime.combine(fecha, time.min))


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
        cliente = Cliente.objects.filter(pk=int(cliente_id)).first()
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

    return render(request, 'core/venta_form.html', {
        'clientes': Cliente.objects.order_by('apellido', 'nombre'),
        'productos': Producto.objects.filter(estado__iexact='activo').order_by('nombre'),
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
    estado = request.GET.get('estado', '').strip()
    cliente_id = request.GET.get('cliente', '').strip()
    producto_id = request.GET.get('producto', '').strip()

    desde = _parse_fecha(desde_txt) if desde_txt else None
    hasta = _parse_fecha(hasta_txt) if hasta_txt else None
    if desde_txt and desde is None:
        errores.append('La fecha "desde" no es válida.')
    if hasta_txt and hasta is None:
        errores.append('La fecha "hasta" no es válida.')
    if desde and hasta and desde > hasta:
        errores.append('La fecha "desde" no puede ser posterior a "hasta".')
        desde = hasta = None

    ventas = Venta.objects.select_related('cliente', 'usuario')
    if desde:
        ventas = ventas.filter(fecha_hora__gte=_inicio_dia(desde))
    if hasta:
        ventas = ventas.filter(fecha_hora__lt=_inicio_dia(hasta + timedelta(days=1)))
    if estado in (ESTADO_CONFIRMADA, ESTADO_ANULADA):
        ventas = ventas.filter(estado=estado)
    if cliente_id.isdecimal():
        ventas = ventas.filter(cliente_id=int(cliente_id))
    if producto_id.isdecimal():
        ventas = ventas.filter(
            id_venta__in=DetalleVenta.objects.filter(
                producto_id=int(producto_id)
            ).values('venta_id')
        )

    total_confirmadas = (
        ventas.filter(estado=ESTADO_CONFIRMADA).aggregate(t=Sum('total'))['t'] or 0
    )
    ventas = list(ventas.order_by('-fecha_hora', '-id_venta'))

    return render(request, 'core/venta_lista.html', {
        'ventas': ventas,
        'total_confirmadas': total_confirmadas,
        'errores': errores,
        'clientes': Cliente.objects.order_by('apellido', 'nombre'),
        'productos': Producto.objects.order_by('nombre'),
        'filtros': {
            'desde': desde_txt,
            'hasta': hasta_txt,
            'estado': estado,
            'cliente': cliente_id,
            'producto': producto_id,
        },
    })


def _datos_venta(pk):
    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'usuario', 'usuario_anulacion'),
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


@permiso_requerido(PERMISO_ANULAR)
@require_http_methods(['GET', 'POST'])
def venta_anular(request, pk):
    venta, detalles = _datos_venta(pk)

    if venta.estado != ESTADO_CONFIRMADA:
        messages.error(request, 'Solo se pueden anular ventas en estado Confirmada.')
        return redirect('venta_detalle', pk=pk)

    error = None
    motivo = ''

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if len(motivo) < 5:
            error = 'Escribí el motivo de la anulación (mínimo 5 caracteres).'
        elif len(motivo) > 200:
            error = 'El motivo no puede superar los 200 caracteres.'
        else:
            with transaction.atomic():
                venta_bloqueada = Venta.objects.select_for_update().get(pk=pk)
                if venta_bloqueada.estado != ESTADO_CONFIRMADA:
                    messages.error(request, 'La venta ya fue anulada.')
                    return redirect('venta_detalle', pk=pk)

                lineas = list(DetalleVenta.objects.filter(venta=venta_bloqueada))
                productos = {
                    p.pk: p
                    for p in Producto.objects.select_for_update()
                    .filter(pk__in=[d.producto_id for d in lineas])
                    .order_by('pk')
                }
                for d in lineas:
                    producto = productos[d.producto_id]
                    producto.stock_actual = (producto.stock_actual or 0) + d.cantidad
                    producto.save(update_fields=['stock_actual'])

                venta_bloqueada.estado = ESTADO_ANULADA
                venta_bloqueada.fecha_anulacion = timezone.now()
                venta_bloqueada.motivo_anulacion = motivo
                venta_bloqueada.usuario_anulacion = _usuario_actual(request)
                venta_bloqueada.save(update_fields=[
                    'estado', 'fecha_anulacion', 'motivo_anulacion', 'usuario_anulacion',
                ])

            messages.success(
                request,
                f'Venta {venta.numero_comprobante} anulada. El stock fue devuelto.'
            )
            return redirect('venta_detalle', pk=pk)

    return render(request, 'core/venta_anular.html', {
        'venta': venta,
        'detalles': detalles,
        'error': error,
        'motivo': motivo,
    })
