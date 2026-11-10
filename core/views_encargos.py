from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auditoria import registrar_auditoria
from .auth_utils import permiso_requerido
from .models import Cliente, DetalleEncargo, Encargo, Producto
from .views_hito3 import MEDIOS_PAGO, _hoy, _leer_items, _parse_fecha, _usuario_actual

PERMISO_VER = 'ver_ventas'
PERMISO_REGISTRAR = 'registrar_venta'
PERMISO_COMPROBANTE = 'emitir_comprobante'
PERMISO_CANCELAR = 'cancelar_encargo'

ESTADOS = [Encargo.ESTADO_PENDIENTE, Encargo.ESTADO_ENTREGADO, Encargo.ESTADO_CANCELADO]
MAX_TEXTO = 200
MAX_IMPORTE = Decimal('99999999.99')
MAX_FILAS = 500


def _leer_senia(texto, errores):
    texto = texto.strip().replace(',', '.')
    if not texto:
        return Decimal('0.00')
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        errores.append('La seña debe ser un número válido.')
        return None
    if not valor.is_finite():
        errores.append('La seña debe ser un número válido.')
        return None
    if valor < 0:
        errores.append('La seña no puede ser negativa.')
        return None
    if valor > MAX_IMPORTE:
        errores.append('La seña supera el máximo permitido.')
        return None
    if valor != valor.quantize(Decimal('0.01')):
        errores.append('La seña admite como máximo 2 decimales.')
        return None
    return valor


def _rango_fechas(request, errores):
    desde_txt = request.GET.get('desde', '').strip()
    hasta_txt = request.GET.get('hasta', '').strip()
    desde = _parse_fecha(desde_txt) if desde_txt else None
    hasta = _parse_fecha(hasta_txt) if hasta_txt else None
    if desde_txt and desde is None:
        errores.append('La fecha "desde" no es válida.')
    if hasta_txt and hasta is None:
        errores.append('La fecha "hasta" no es válida.')
    if desde and hasta and desde > hasta:
        errores.append('La fecha "desde" no puede ser posterior a "hasta".')
        desde = hasta = None
    return desde_txt, hasta_txt, desde, hasta


def _registrar_encargo(request, datos, ids, cantidades, errores):
    cliente = None
    if datos['cliente'].isdecimal():
        cliente = Cliente.objects.filter(pk=int(datos['cliente']), activo=True).first()
    if cliente is None:
        errores.append('Elegí un cliente de la lista.')

    hoy = _hoy()
    fecha_entrega = _parse_fecha(datos['fecha_entrega'])
    if fecha_entrega is None:
        errores.append('Indicá una fecha de entrega válida.')
    elif fecha_entrega < hoy:
        errores.append('La fecha de entrega no puede ser anterior a hoy.')

    senia = _leer_senia(datos['senia'], errores)

    medio_pago = datos['medio_pago']
    if medio_pago and medio_pago not in MEDIOS_PAGO:
        errores.append('Elegí un medio de pago de la lista.')
    elif senia and not medio_pago:
        errores.append('Elegí el medio de pago de la seña.')

    observacion = datos['observacion']
    if len(observacion) > MAX_TEXTO:
        errores.append(f'La observación no puede superar {MAX_TEXTO} caracteres.')

    items = _leer_items(ids, cantidades, errores)
    if not items:
        errores.append('Agregá al menos un producto al encargo.')

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
                errores.append(f'«{producto.nombre}» está inactivo y no se puede encargar.')
            elif (producto.stock_actual or 0) < cant:
                errores.append(
                    f'Stock insuficiente de «{producto.nombre}»: '
                    f'disponible {producto.stock_actual or 0}, pedido {cant}.'
                )

        if errores:
            return None

        total = sum(
            (productos[pid].precio_unitario * cant for pid, cant in items.items()),
            Decimal('0'),
        )
        if total > MAX_IMPORTE:
            errores.append('El total supera el máximo permitido.')
            return None
        if senia > total:
            errores.append('La seña no puede superar el total del encargo.')
            return None

        encargo = Encargo.objects.create(
            fecha_pedido=hoy,
            fecha_entrega_prevista=fecha_entrega,
            senia=senia,
            total=total,
            estado=Encargo.ESTADO_PENDIENTE,
            medio_pago=medio_pago or None,
            observacion=observacion or None,
            usuario=_usuario_actual(request),
            cliente=cliente,
        )

        for pid in sorted(items):
            producto = productos[pid]
            cant = items[pid]
            DetalleEncargo.objects.create(
                encargo=encargo,
                producto=producto,
                cantidad=cant,
                precio_unitario=producto.precio_unitario,
                subtotal=producto.precio_unitario * cant,
            )
            producto.stock_actual = (producto.stock_actual or 0) - cant
            producto.save(update_fields=['stock_actual'])

    return encargo


@permiso_requerido(PERMISO_REGISTRAR)
@require_http_methods(['GET', 'POST'])
def encargo_crear(request):
    errores = []
    datos = {'cliente': '', 'medio_pago': '', 'fecha_entrega': '', 'senia': '', 'observacion': ''}
    lineas = []

    if request.method == 'POST':
        for campo in datos:
            datos[campo] = request.POST.get(campo, '').strip()
        ids = request.POST.getlist('producto')
        cantidades = request.POST.getlist('cantidad')
        lineas = [{'producto': p, 'cantidad': c} for p, c in zip(ids, cantidades)]

        encargo = _registrar_encargo(request, datos, ids, cantidades, errores)
        if encargo is not None:
            messages.success(
                request,
                f'Encargo {encargo.numero_comprobante} registrado. El stock fue descontado.'
            )
            return redirect('encargo_detalle', pk=encargo.pk)

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

    return render(request, 'core/encargo_form.html', {
        'clientes': Cliente.objects.filter(activo=True).order_by('apellido', 'nombre'),
        'productos_json': productos_json,
        'medios_pago': MEDIOS_PAGO,
        'errores': list(dict.fromkeys(errores)),
        'datos': datos,
        'lineas': lineas,
        'hoy': _hoy().isoformat(),
    })


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def encargo_lista(request):
    errores = []
    desde_txt, hasta_txt, desde, hasta = _rango_fechas(request, errores)
    estado = request.GET.get('estado', '').strip()
    cliente_id = request.GET.get('cliente', '').strip()
    producto_id = request.GET.get('producto', '').strip()

    encargos = Encargo.objects.all()
    if desde:
        encargos = encargos.filter(fecha_pedido__gte=desde)
    if hasta:
        encargos = encargos.filter(fecha_pedido__lte=hasta)
    if estado in ESTADOS:
        encargos = encargos.filter(estado=estado)
    if cliente_id.isdecimal():
        encargos = encargos.filter(cliente_id=int(cliente_id))
    if producto_id.isdecimal():
        encargos = encargos.filter(
            id_encargo__in=DetalleEncargo.objects.filter(
                producto_id=int(producto_id)
            ).values('encargo_id')
        )

    encargos = list(
        encargos.select_related('cliente', 'usuario')
        .annotate(
            cant_items=Sum('detalleencargo__cantidad'),
            sin_preparar=Count('detalleencargo', filter=Q(detalleencargo__preparado=False)),
        )
        .order_by('-id_encargo')
    )

    pendientes = [e for e in encargos if e.estado == Encargo.ESTADO_PENDIENTE]

    return render(request, 'core/encargo_lista.html', {
        'encargos': encargos,
        'cantidad_pendientes': len(pendientes),
        'total_pendiente': sum((e.total for e in pendientes), Decimal('0')),
        'saldo_pendiente': sum((e.saldo for e in pendientes), Decimal('0')),
        'errores': errores,
        'estados': ESTADOS,
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


def _datos_encargo(pk):
    encargo = get_object_or_404(
        Encargo.objects.select_related('cliente', 'usuario', 'usuario_anulacion'),
        pk=pk,
    )
    detalles = (
        DetalleEncargo.objects.filter(encargo=encargo)
        .select_related('producto')
        .order_by('id')
    )
    return encargo, detalles


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def encargo_detalle(request, pk):
    encargo, detalles = _datos_encargo(pk)
    return render(request, 'core/encargo_detalle.html', {
        'encargo': encargo,
        'detalles': detalles,
        'pendiente': encargo.estado == Encargo.ESTADO_PENDIENTE,
    })


@permiso_requerido(PERMISO_COMPROBANTE)
@require_http_methods(['GET'])
def encargo_comprobante(request, pk):
    encargo, detalles = _datos_encargo(pk)
    return render(request, 'core/encargo_comprobante.html', {
        'encargo': encargo,
        'detalles': detalles,
    })


@permiso_requerido(PERMISO_REGISTRAR)
@require_http_methods(['POST'])
def encargo_entregar(request, pk):
    with transaction.atomic():
        encargo = get_object_or_404(Encargo.objects.select_for_update(), pk=pk)
        if encargo.estado != Encargo.ESTADO_PENDIENTE:
            messages.error(request, 'Solo se pueden entregar encargos pendientes.')
            return redirect('encargo_detalle', pk=pk)
        encargo.estado = Encargo.ESTADO_ENTREGADO
        encargo.fecha_entrega_real = timezone.now()
        encargo.save(update_fields=['estado', 'fecha_entrega_real'])
    messages.success(request, f'Encargo {encargo.numero_comprobante} marcado como entregado.')
    return redirect('encargo_detalle', pk=pk)


@permiso_requerido(PERMISO_CANCELAR)
@require_http_methods(['POST'])
def encargo_cancelar(request, pk):
    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, 'Indicá el motivo de la cancelación.')
        return redirect('encargo_detalle', pk=pk)
    if len(motivo) > MAX_TEXTO:
        messages.error(request, f'El motivo no puede superar {MAX_TEXTO} caracteres.')
        return redirect('encargo_detalle', pk=pk)

    usuario = _usuario_actual(request)
    with transaction.atomic():
        encargo = get_object_or_404(Encargo.objects.select_for_update(), pk=pk)
        if encargo.estado != Encargo.ESTADO_PENDIENTE:
            messages.error(request, 'Solo se pueden cancelar encargos pendientes.')
            return redirect('encargo_detalle', pk=pk)

        detalles = list(DetalleEncargo.objects.filter(encargo=encargo))
        productos = {
            p.pk: p
            for p in Producto.objects.select_for_update()
            .filter(pk__in=[d.producto_id for d in detalles])
            .order_by('pk')
        }
        for d in detalles:
            producto = productos[d.producto_id]
            producto.stock_actual = (producto.stock_actual or 0) + d.cantidad
            producto.save(update_fields=['stock_actual'])

        ahora = timezone.now()
        Encargo.objects.filter(pk=encargo.pk).update(
            estado=Encargo.ESTADO_CANCELADO,
            fecha_anulacion=ahora,
            motivo_anulacion=motivo,
            usuario_anulacion=usuario,
        )
        registrar_auditoria(
            'encargo',
            encargo.pk,
            'ANULACION',
            {'estado': encargo.estado},
            {
                'estado': Encargo.ESTADO_CANCELADO,
                'fecha_anulacion': ahora,
                'motivo_anulacion': motivo,
                'usuario_anulacion_id': usuario.pk,
            },
        )
    messages.success(request, f'Encargo {encargo.numero_comprobante} cancelado. El stock fue repuesto.')
    return redirect('encargo_detalle', pk=pk)


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def produccion_lista(request):
    errores = []
    desde_txt, hasta_txt, desde, hasta = _rango_fechas(request, errores)
    estado = request.GET.get('estado', Encargo.ESTADO_PENDIENTE).strip()
    if estado != 'Todos' and estado not in ESTADOS:
        estado = Encargo.ESTADO_PENDIENTE
    cliente_id = request.GET.get('cliente', '').strip()
    producto_id = request.GET.get('producto', '').strip()

    items = DetalleEncargo.objects.all()
    if estado != 'Todos':
        items = items.filter(encargo__estado=estado)
    if desde:
        items = items.filter(encargo__fecha_entrega_prevista__gte=desde)
    if hasta:
        items = items.filter(encargo__fecha_entrega_prevista__lte=hasta)
    if cliente_id.isdecimal():
        items = items.filter(encargo__cliente_id=int(cliente_id))
    if producto_id.isdecimal():
        items = items.filter(producto_id=int(producto_id))

    resumen = (
        items.values('encargo__fecha_entrega_prevista', 'producto__nombre')
        .annotate(unidades=Sum('cantidad'), pedidos=Count('encargo', distinct=True))
        .order_by('encargo__fecha_entrega_prevista', 'producto__nombre')
    )
    grupos = []
    for fila in resumen:
        fecha = fila['encargo__fecha_entrega_prevista']
        if not grupos or grupos[-1]['fecha'] != fecha:
            grupos.append({'fecha': fecha, 'filas': [], 'unidades': 0})
        grupos[-1]['filas'].append({
            'producto': fila['producto__nombre'],
            'unidades': fila['unidades'],
            'pedidos': fila['pedidos'],
        })
        grupos[-1]['unidades'] += fila['unidades']

    total_filas = items.count()
    filas = list(
        items.select_related('producto', 'encargo__cliente')
        .order_by('encargo__fecha_entrega_prevista', 'encargo_id', 'producto__nombre')[:MAX_FILAS]
    )

    return render(request, 'core/produccion_lista.html', {
        'grupos': grupos,
        'filas': filas,
        'total_filas': total_filas,
        'max_filas': MAX_FILAS,
        'unidades_total': sum(g['unidades'] for g in grupos),
        'pedidos_total': items.values('encargo_id').distinct().count(),
        'errores': errores,
        'estados': ESTADOS,
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


@permiso_requerido(PERMISO_REGISTRAR)
@require_http_methods(['POST'])
def encargo_item_preparado(request, pk):
    with transaction.atomic():
        item = get_object_or_404(DetalleEncargo.objects.select_for_update().select_related('encargo'), pk=pk)
        if item.encargo.estado == Encargo.ESTADO_PENDIENTE:
            item.preparado = request.POST.get('preparado') == '1'
            item.save(update_fields=['preparado'])
    volver = request.POST.get('volver', '')
    if not volver.startswith(reverse('detalle_encargo_lista')):
        volver = reverse('detalle_encargo_lista')
    return redirect(volver)
