from datetime import timedelta
from decimal import ROUND_HALF_UP, ROUND_UP, Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auditoria import registrar_auditoria
from .auth_utils import permiso_requerido
from .models import Cliente, DetalleEncargo, Encargo, NotaCredito, Producto
from .views_hito3 import MEDIOS_PAGO, MESES, ZONA_LOCAL, _hoy, _leer_items, _parse_fecha, _usuario_actual

PERMISO_VER = 'ver_ventas'
PERMISO_REGISTRAR = 'registrar_venta'
PERMISO_COMPROBANTE = 'emitir_comprobante'
PERMISO_CANCELAR = 'cancelar_encargo'

ESTADOS = [Encargo.ESTADO_PENDIENTE, Encargo.ESTADO_ENTREGADO, Encargo.ESTADO_CANCELADO]
MAX_TEXTO = 200
MAX_IMPORTE = Decimal('99999999.99')
MAX_DIAS_ENTREGA = 7


def _leer_senia(texto, errores):
    texto = texto.strip().replace(',', '.')
    if not texto:
        errores.append('Indicá la seña.')
        return None
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


def _preparacion_iniciada(encargo):
    return DetalleEncargo.objects.filter(encargo=encargo, preparado=True).exists()


def _politica_devolucion(encargo, fecha_cancelacion, iniciada):
    if not iniciada:
        return Decimal('100'), 'La preparación del encargo no había comenzado: se devuelve el 100% de la seña.'
    pedido = encargo.fecha_pedido
    entrega = encargo.fecha_entrega_prevista
    if entrega is None:
        return Decimal('0'), 'El encargo no tiene fecha de entrega: no corresponde devolución.'
    dias_antes = (entrega - fecha_cancelacion).days
    if pedido is not None:
        if (entrega - pedido).days <= 1:
            return Decimal('0'), 'El encargo se pidió para el día siguiente: no corresponde devolución.'
        if (fecha_cancelacion - pedido).days <= 1:
            return Decimal('100'), 'Cancelado el mismo día o el día siguiente al pedido: se devuelve el 100% de la seña.'
    if dias_antes <= 0:
        return Decimal('0'), 'Cancelado el día de la entrega: no corresponde devolución.'
    if dias_antes == 1:
        return Decimal('2'), 'Cancelado 1 día antes de la entrega: se devuelve el 2% de la seña.'
    if dias_antes <= 4:
        return Decimal('50'), f'Cancelado {dias_antes} días antes de la entrega: se devuelve el 50% de la seña.'
    return Decimal('100'), f'Cancelado {dias_antes} días antes de la entrega: se devuelve el 100% de la seña.'


def _merma_porcentaje(encargo, fecha_cancelacion, iniciada):
    if not iniciada:
        return Decimal('0')
    pedido = encargo.fecha_pedido
    entrega = encargo.fecha_entrega_prevista
    if entrega is None:
        return Decimal('0')
    if pedido is not None:
        if (entrega - pedido).days <= 1:
            return Decimal('90')
        if (fecha_cancelacion - pedido).days <= 1:
            return Decimal('0')
    dias_antes = (entrega - fecha_cancelacion).days
    if dias_antes <= 1:
        return Decimal('90')
    if dias_antes <= 4:
        return Decimal('50')
    return Decimal('0')


def _unidades_merma(cantidad, porcentaje):
    return int((Decimal(cantidad) * porcentaje / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _comprometido(producto_ids, excluir_encargo=None):
    pendientes = DetalleEncargo.objects.filter(
        producto_id__in=producto_ids, encargo__estado=Encargo.ESTADO_PENDIENTE,
    )
    if excluir_encargo is not None:
        pendientes = pendientes.exclude(encargo=excluir_encargo)
    return {
        fila['producto_id']: fila['total'] or 0
        for fila in pendientes.values('producto_id').annotate(total=Sum('cantidad'))
    }


def _monto_devolucion(encargo, porcentaje):
    senia = encargo.senia or Decimal('0')
    return (senia * porcentaje / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


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
    elif fecha_entrega > hoy + timedelta(days=MAX_DIAS_ENTREGA):
        errores.append(f'La entrega no puede ser más de {MAX_DIAS_ENTREGA} días después del pedido.')

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

        comprometido = _comprometido(list(items))
        for pid, cant in items.items():
            producto = productos.get(pid)
            if producto is None:
                errores.append('Hay un producto que ya no existe.')
                continue
            disponible = (producto.stock_actual or 0) - comprometido.get(pid, 0)
            if (producto.estado or '').lower() != 'activo':
                errores.append(f'«{producto.nombre}» está inactivo y no se puede encargar.')
            elif disponible < cant:
                errores.append(
                    f'Stock insuficiente de «{producto.nombre}»: '
                    f'disponible {max(disponible, 0)} (stock {producto.stock_actual or 0} menos lo reservado '
                    f'en encargos pendientes), pedido {cant}.'
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
        if senia * 2 < total:
            minimo = (total / 2).quantize(Decimal('0.01'), rounding=ROUND_UP)
            errores.append(f'La seña debe ser al menos el 50% del total: mínimo ${minimo} sobre un total de ${total:.2f}.')
            return None

        encargo = Encargo.objects.create(
            fecha_pedido=hoy,
            fecha_hora_registro=timezone.now(),
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
                f'Encargo {encargo.numero_comprobante} registrado. El stock se descontará al entregarlo.'
            )
            return redirect('encargo_detalle', pk=encargo.pk)

    productos = (
        Producto.objects.filter(estado__iexact='activo')
        .select_related('categoria')
        .order_by('nombre')
    )
    comprometido = _comprometido([p.pk for p in productos])
    productos_json = [
        {
            'id': p.pk,
            'nombre': p.nombre,
            'precio': str(p.precio_unitario),
            'stock': max((p.stock_actual or 0) - comprometido.get(p.pk, 0), 0),
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
        'hoy_max': (_hoy() + timedelta(days=MAX_DIAS_ENTREGA)).isoformat(),
    })


def _resumen_mes_encargos(valor_elegido):
    hoy = _hoy()
    actual = (hoy.year, hoy.month)
    meses = {actual}
    for fecha in Encargo.objects.exclude(fecha_entrega_prevista=None).values_list('fecha_entrega_prevista', flat=True):
        meses.add((fecha.year, fecha.month))
    try:
        anio, mes = (int(p) for p in valor_elegido.split('-'))
    except (AttributeError, ValueError):
        anio, mes = actual
    if (anio, mes) not in meses:
        anio, mes = actual
    del_mes = list(Encargo.objects.filter(
        fecha_entrega_prevista__year=anio, fecha_entrega_prevista__month=mes,
    ))
    vigentes = [e for e in del_mes if e.estado != Encargo.ESTADO_CANCELADO]
    pendientes = [e for e in del_mes if e.estado == Encargo.ESTADO_PENDIENTE]
    resumen = {
        'valor': f'{anio}-{mes:02d}',
        'cantidad': len(del_mes),
        'pendientes': len(pendientes),
        'entregados': sum(1 for e in del_mes if e.estado == Encargo.ESTADO_ENTREGADO),
        'cancelados': sum(1 for e in del_mes if e.estado == Encargo.ESTADO_CANCELADO),
        'total': sum((e.total for e in vigentes), Decimal('0')),
        'senias': sum((e.senia or 0 for e in vigentes), Decimal('0')),
        'saldo': sum((e.saldo for e in pendientes if not e.saldo_pagado), Decimal('0')),
    }
    opciones = [
        {'valor': f'{a}-{m:02d}', 'texto': f'{MESES[m - 1]} de {a}'}
        for a, m in sorted(meses, reverse=True)
    ]
    return opciones, resumen


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

    opciones_mes, resumen_mes = _resumen_mes_encargos(request.GET.get('mes', '').strip())

    return render(request, 'core/encargo_lista.html', {
        'encargos': encargos,
        'opciones_mes': opciones_mes,
        'resumen_mes': resumen_mes,
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
    iniciada = any(d.preparado for d in detalles)
    devolucion = None
    if encargo.estado == Encargo.ESTADO_PENDIENTE and encargo.senia:
        porcentaje, explicacion = _politica_devolucion(encargo, _hoy(), iniciada)
        devolucion = {
            'porcentaje': porcentaje,
            'explicacion': explicacion,
            'monto': _monto_devolucion(encargo, porcentaje),
        }
    merma = None
    if encargo.estado == Encargo.ESTADO_PENDIENTE:
        merma = _merma_porcentaje(encargo, _hoy(), iniciada)
    return render(request, 'core/encargo_detalle.html', {
        'encargo': encargo,
        'detalles': detalles,
        'pendiente': encargo.estado == Encargo.ESTADO_PENDIENTE,
        'devolucion': devolucion,
        'merma': merma,
        'nota_credito': NotaCredito.objects.filter(encargo=encargo).select_related('usuario').first(),
        'medios_pago': MEDIOS_PAGO,
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
        if not encargo.saldo_pagado:
            messages.error(request, f'No se puede entregar: primero hay que cobrar el saldo (${encargo.saldo:.2f}).')
            return redirect('encargo_detalle', pk=pk)
        detalles = list(DetalleEncargo.objects.filter(encargo=encargo))
        productos = {
            p.pk: p
            for p in Producto.objects.select_for_update()
            .filter(pk__in=[d.producto_id for d in detalles])
            .order_by('pk')
        }
        faltantes = [
            f'«{productos[d.producto_id].nombre}» (stock {productos[d.producto_id].stock_actual or 0}, se necesitan {d.cantidad})'
            for d in detalles
            if (productos[d.producto_id].stock_actual or 0) < d.cantidad
        ]
        if faltantes:
            messages.error(request, 'No se puede entregar: stock insuficiente de ' + ', '.join(faltantes) + '.')
            return redirect('encargo_detalle', pk=pk)
        for d in detalles:
            producto = productos[d.producto_id]
            producto.stock_actual = (producto.stock_actual or 0) - d.cantidad
            producto.save(update_fields=['stock_actual'])
        encargo.estado = Encargo.ESTADO_ENTREGADO
        encargo.fecha_entrega_real = timezone.now()
        encargo.save(update_fields=['estado', 'fecha_entrega_real'])
    messages.success(request, f'Encargo {encargo.numero_comprobante} marcado como entregado. El stock fue descontado.')
    return redirect('encargo_detalle', pk=pk)


@permiso_requerido(PERMISO_REGISTRAR)
@require_http_methods(['POST'])
def encargo_pagar_saldo(request, pk):
    medio = request.POST.get('medio_pago_saldo', '').strip()
    if medio not in MEDIOS_PAGO:
        messages.error(request, 'Elegí el medio de pago del saldo.')
        return redirect('encargo_detalle', pk=pk)
    with transaction.atomic():
        encargo = get_object_or_404(Encargo.objects.select_for_update(), pk=pk)
        if encargo.estado != Encargo.ESTADO_PENDIENTE:
            messages.error(request, 'Solo se puede cobrar el saldo de encargos pendientes.')
            return redirect('encargo_detalle', pk=pk)
        if encargo.saldo_pagado:
            messages.error(request, 'El saldo de este encargo ya está cobrado.')
            return redirect('encargo_detalle', pk=pk)
        encargo.fecha_pago_saldo = timezone.now()
        encargo.medio_pago_saldo = medio
        encargo.usuario_pago_saldo = _usuario_actual(request)
        encargo.save(update_fields=['fecha_pago_saldo', 'medio_pago_saldo', 'usuario_pago_saldo'])
    messages.success(request, f'Saldo de ${encargo.saldo:.2f} cobrado ({medio}). Ya se puede marcar como entregado.')
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
        if encargo.fecha_pago_saldo is not None:
            messages.error(request, 'No se puede cancelar: el saldo ya fue cobrado. El encargo solo puede entregarse.')
            return redirect('encargo_detalle', pk=pk)

        detalles = list(DetalleEncargo.objects.select_for_update().filter(encargo=encargo))
        iniciada = any(d.preparado for d in detalles)
        porcentaje, explicacion = _politica_devolucion(encargo, _hoy(), iniciada)
        devolucion = _monto_devolucion(encargo, porcentaje)
        medio_devolucion = ''
        if devolucion > 0:
            medio_devolucion = request.POST.get('medio_devolucion', '').strip()
            if medio_devolucion not in MEDIOS_PAGO:
                messages.error(request, 'Elegí cómo se devuelve el dinero.')
                return redirect('encargo_detalle', pk=pk)
            if encargo.medio_pago and medio_devolucion != encargo.medio_pago:
                messages.error(
                    request,
                    f'El dinero se devuelve por el mismo medio con el que se pagó la seña ({encargo.medio_pago}). '
                    'Elegí ese medio para poder cancelar.',
                )
                return redirect('encargo_detalle', pk=pk)

        productos = {
            p.pk: p
            for p in Producto.objects.select_for_update()
            .filter(pk__in=[d.producto_id for d in detalles])
            .order_by('pk')
        }
        merma = _merma_porcentaje(encargo, _hoy(), iniciada)
        if merma > 0:
            for d in detalles:
                producto = productos[d.producto_id]
                unidades = min(_unidades_merma(d.cantidad, merma), max(producto.stock_actual or 0, 0))
                if unidades:
                    producto.stock_actual = (producto.stock_actual or 0) - unidades
                    producto.save(update_fields=['stock_actual'])

        ahora = timezone.now()
        Encargo.objects.filter(pk=encargo.pk).update(
            estado=Encargo.ESTADO_CANCELADO,
            fecha_anulacion=ahora,
            motivo_anulacion=motivo,
            usuario_anulacion=usuario,
        )
        nota = None
        if devolucion > 0:
            nota = NotaCredito.objects.create(
                encargo=encargo,
                fecha_hora=ahora,
                monto=devolucion,
                porcentaje=porcentaje,
                medio_devolucion=medio_devolucion,
                motivo=motivo,
                usuario=usuario,
            )
        despues = {
            'estado': Encargo.ESTADO_CANCELADO,
            'fecha_anulacion': ahora,
            'motivo_anulacion': motivo,
            'usuario_anulacion_id': usuario.pk,
        }
        despues['porcentaje_devolucion'] = porcentaje
        despues['merma_porcentaje'] = merma
        if nota:
            despues['nota_credito'] = nota.numero_comprobante
            despues['monto_devuelto'] = devolucion
        registrar_auditoria('encargo', encargo.pk, 'ANULACION', {'estado': encargo.estado}, despues)
    mensaje = f'Encargo {encargo.numero_comprobante} cancelado.'
    if merma > 0:
        mensaje += f' Se descontó del stock el {merma:.0f}% de los productos como merma.'
    else:
        mensaje += ' No se descontó stock.'
    if nota:
        mensaje += f' Se emitió la nota de crédito {nota.numero_comprobante} por ${devolucion:.2f}.'
    elif encargo.senia:
        mensaje += f' {explicacion}'
    messages.success(request, mensaje)
    return redirect('encargo_detalle', pk=pk)


@permiso_requerido(PERMISO_COMPROBANTE)
@require_http_methods(['GET'])
def encargo_nota_credito(request, pk):
    nota = get_object_or_404(
        NotaCredito.objects.select_related('encargo__cliente', 'usuario'),
        encargo_id=pk,
    )
    explicacion = ''
    if nota.encargo.fecha_anulacion:
        fecha = timezone.localtime(nota.encargo.fecha_anulacion, ZONA_LOCAL).date()
        explicacion = _politica_devolucion(nota.encargo, fecha, _preparacion_iniciada(nota.encargo))[1]
    return render(request, 'core/nota_credito_comprobante.html', {
        'nota': nota,
        'encargo': nota.encargo,
        'explicacion': explicacion,
    })


@permiso_requerido(PERMISO_REGISTRAR)
@require_http_methods(['POST'])
def encargo_item_preparado(request, pk):
    with transaction.atomic():
        item = get_object_or_404(DetalleEncargo.objects.select_for_update().select_related('encargo'), pk=pk)
        if item.encargo.estado == Encargo.ESTADO_PENDIENTE and not item.preparado and request.POST.get('preparado') == '1':
            item.preparado = True
            item.save(update_fields=['preparado'])
    return redirect('encargo_detalle', pk=item.encargo_id)
