"""Recetas y registro de producción.

Una receta dice cuánto de cada insumo lleva UNA unidad de un producto.
Al registrar una producción (por ejemplo, 200 medialunas), el sistema:
  1. calcula cuánto se usa de cada insumo (receta x cantidad),
  2. verifica que alcance el stock de todos,
  3. descuenta los insumos con un movimiento de Salida cada uno,
  4. suma la cantidad producida al stock del producto,
  5. revisa la alerta de stock bajo de cada insumo usado.
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .alertas import al_mover_insumo, aviso_para_pantalla
from .auth_utils import permiso_requerido
from .models import Insumo, MovimientoInsumo, Produccion, Producto, Receta
from .views_hito3 import _usuario_actual

PERMISO_VER = 'ver_productos'
PERMISO_EDITAR = 'editar_stock'
MAX_POR_UNIDAD = Decimal('1000')
MAX_PRODUCCION = 100000
FILAS_POR_PAGINA = 30
MIL = Decimal('0.001')


def _numero(valor):
    """Muestra un Decimal sin ceros de más (0.0250 → 0.025)."""
    texto = f'{valor.normalize():f}'
    return texto


def _consumo(receta, cantidad):
    """Cantidad de insumo que usa una tanda (redondeada a milésimas, como el stock de insumos)."""
    return (receta.cantidad * cantidad).quantize(MIL, rounding=ROUND_HALF_UP)


def _detalle(producto, cantidad):
    """Arma la lista de insumos necesarios para producir `cantidad` unidades y si alcanza el stock."""
    filas = []
    for r in Receta.objects.filter(producto=producto).select_related('insumo').order_by('insumo__nombre'):
        necesario = _consumo(r, cantidad)
        if necesario <= 0:
            continue
        insumo = r.insumo
        quedaria = insumo.stock_actual - necesario
        filas.append({
            'insumo': insumo,
            'por_unidad': _numero(r.cantidad),
            'necesario': necesario,
            'disponible': insumo.stock_actual,
            'quedaria': quedaria,
            'falta': not insumo.activo or quedaria < 0,
            'bajo_minimo': quedaria >= 0 and insumo.stock_minimo > 0 and quedaria <= insumo.stock_minimo,
        })
    return filas


def _leer_cantidad(texto):
    texto = (texto or '').strip()
    if not texto.isdecimal() or not (1 <= int(texto) <= MAX_PRODUCCION):
        return None
    return int(texto)


@permiso_requerido(PERMISO_EDITAR)
@require_http_methods(['GET', 'POST'])
def receta_editar(request, pk):
    producto = get_object_or_404(Producto.objects.select_related('categoria'), pk=pk)
    actuales = {r.insumo_id: r for r in Receta.objects.filter(producto=producto)}
    insumos = list(Insumo.objects.filter(activo=True).order_by('nombre'))
    # Los insumos dados de baja que ya están en la receta también se muestran, para poder quitarlos.
    insumos += [r.insumo for r in actuales.values() if not r.insumo.activo]
    errores = []
    valores = {i.pk: (_numero(actuales[i.pk].cantidad) if i.pk in actuales else '') for i in insumos}

    if request.method == 'POST':
        nuevos = {}
        for insumo in insumos:
            texto = request.POST.get(f'insumo_{insumo.pk}', '').strip().replace(',', '.')
            valores[insumo.pk] = texto
            if not texto:
                nuevos[insumo.pk] = None
                continue
            try:
                cantidad = Decimal(texto)
            except InvalidOperation:
                errores.append(f'«{insumo.nombre}»: escribí un número válido.')
                continue
            if not cantidad.is_finite() or cantidad < 0 or cantidad > MAX_POR_UNIDAD:
                errores.append(f'«{insumo.nombre}»: la cantidad debe estar entre 0 y {MAX_POR_UNIDAD}.')
                continue
            if cantidad != cantidad.quantize(Decimal('0.0001')):
                errores.append(f'«{insumo.nombre}»: usá como máximo 4 decimales.')
                continue
            nuevos[insumo.pk] = cantidad if cantidad > 0 else None

        if not any(nuevos.values()) and not errores:
            errores.append('La receta tiene que llevar al menos un insumo.')

        if not errores:
            with transaction.atomic():
                for insumo in insumos:
                    cantidad = nuevos.get(insumo.pk)
                    fila = actuales.get(insumo.pk)
                    if cantidad is None:
                        if fila is not None:
                            fila.delete()  # fila de vínculo producto-insumo, como insumo_producto
                    elif fila is None:
                        Receta.objects.create(producto=producto, insumo=insumo, cantidad=cantidad)
                    elif fila.cantidad != cantidad:
                        fila.cantidad = cantidad
                        fila.save(update_fields=['cantidad'])
                    if cantidad is not None:
                        insumo.productos.add(producto)  # mantiene al día la columna "Usado en" de Insumos
            messages.success(request, f'Receta de «{producto.nombre}» guardada.')
            return redirect('producto_lista')

    filas = [{'insumo': i, 'valor': valores[i.pk]} for i in insumos]
    return render(request, 'core/receta_form.html', {'producto': producto, 'filas': filas, 'errores': errores})


@permiso_requerido(PERMISO_EDITAR)
@require_http_methods(['GET', 'POST'])
def produccion_crear(request):
    productos = list(
        Producto.objects.filter(estado__iexact='activo', receta__isnull=False).distinct().order_by('nombre')
    )
    sin_receta = Producto.objects.filter(estado__iexact='activo', receta__isnull=True).order_by('nombre')
    datos = request.POST if request.method == 'POST' else request.GET
    producto_txt = datos.get('producto', '').strip()
    cantidad_txt = datos.get('cantidad', '').strip()
    producto = next((p for p in productos if str(p.pk) == producto_txt), None)
    cantidad = _leer_cantidad(cantidad_txt)
    errores = []
    detalle = None

    if producto_txt or cantidad_txt:
        if producto is None:
            errores.append('Elegí un producto de la lista (solo aparecen los que tienen receta).')
        if cantidad is None:
            errores.append(f'La cantidad debe ser un número entero entre 1 y {MAX_PRODUCCION}.')

    if request.method == 'POST' and not errores and producto and cantidad:
        produccion, errores = _registrar(request, producto, cantidad)
        if produccion is not None:
            messages.success(
                request,
                f'Producción {produccion.numero_comprobante} registrada: +{cantidad} «{producto.nombre}» '
                f'(stock {produccion.producto.stock_actual}). Se descontaron los insumos de la receta.',
            )
            return redirect('produccion_lista')

    if producto and cantidad:
        detalle = _detalle(producto, cantidad)

    return render(request, 'core/produccion_form.html', {
        'productos': productos,
        'sin_receta': sin_receta,
        'producto': producto,
        'producto_txt': producto_txt,
        'cantidad_txt': cantidad_txt,
        'cantidad': cantidad,
        'detalle': detalle,
        'puede_confirmar': bool(detalle) and not any(f['falta'] for f in detalle),
        'errores': errores,
    })


def _registrar(request, producto, cantidad):
    """Descuenta los insumos y suma el stock del producto en una sola transacción."""
    errores = []
    usados = []
    with transaction.atomic():
        producto = Producto.objects.select_for_update().get(pk=producto.pk)
        if (producto.estado or '').lower() != 'activo':
            return None, ['El producto está dado de baja.']
        recetas = list(Receta.objects.filter(producto=producto))
        insumos = {
            i.pk: i
            for i in Insumo.objects.select_for_update().filter(pk__in=[r.insumo_id for r in recetas]).order_by('pk')
        }
        consumos = [(insumos[r.insumo_id], _consumo(r, cantidad)) for r in recetas]
        consumos = [(i, c) for i, c in consumos if c > 0]
        if not consumos:
            return None, ['El producto no tiene receta cargada.']
        for insumo, necesario in consumos:
            if not insumo.activo:
                errores.append(f'«{insumo.nombre}» está dado de baja. Dalo de alta o quitalo de la receta.')
            elif insumo.stock_actual < necesario:
                errores.append(
                    f'Falta {insumo.nombre}: hay {_numero(insumo.stock_actual)} {insumo.unidad} '
                    f'y se necesitan {_numero(necesario)} {insumo.unidad}.'
                )
        if errores:
            return None, errores

        ahora = timezone.now()
        usuario = _usuario_actual(request)
        produccion = Produccion.objects.create(producto=producto, cantidad=cantidad, fecha_hora=ahora, usuario=usuario)
        for insumo, necesario in consumos:
            insumo.stock_actual -= necesario
            insumo.save(update_fields=['stock_actual'])
            MovimientoInsumo.objects.create(
                insumo=insumo, tipo=MovimientoInsumo.TIPO_SALIDA, cantidad=necesario,
                stock_resultante=insumo.stock_actual, fecha_hora=ahora,
                motivo=f'Producción {produccion.numero_comprobante}: {cantidad} {producto.nombre}',
                usuario=usuario, produccion=produccion,
            )
            usados.append(insumo)
        producto.stock_actual = (producto.stock_actual or 0) + cantidad
        producto.save(update_fields=['stock_actual'])
        produccion.producto = producto

    # Después de confirmar: alerta de stock bajo de cada insumo usado (y correo si está configurado).
    for insumo in usados:
        alerta = al_mover_insumo(insumo)
        if alerta is not None:
            messages.warning(request, aviso_para_pantalla(alerta))
    return produccion, []


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def produccion_lista(request):
    producciones = Produccion.objects.select_related('producto', 'usuario').prefetch_related('movimientos__insumo')
    pagina = Paginator(producciones.order_by('-fecha_hora', '-id_produccion'), FILAS_POR_PAGINA).get_page(
        request.GET.get('page'),
    )
    return render(request, 'core/produccion_lista.html', {
        'pagina': pagina,
        'paginas': pagina.paginator.get_elided_page_range(pagina.number, on_each_side=2, on_ends=1),
    })
