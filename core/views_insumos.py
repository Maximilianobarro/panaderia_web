from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .alertas import al_mover_insumo, aviso_para_pantalla
from .auth_utils import permiso_requerido
from .forms import InsumoForm
from .models import Insumo, MovimientoInsumo
from .views_hito3 import _usuario_actual

PERMISO_VER = 'ver_productos'
PERMISO_EDITAR = 'editar_stock'
PERMISO_ESTADO = 'dar_baja_alta'

MAX_CANTIDAD = Decimal('999999999.999')
MAX_TEXTO = 200
ORDEN_NIVEL = {'sin': 0, 'bajo': 1, 'cerca': 2}
# Ordenamientos de la tabla: nombre (A-Z / Z-A), stock (mayor a menor / menor a mayor)
# y situación (más stock respecto del mínimo primero / menos primero).
ORDENES = {'nombre', '-nombre', 'stock', '-stock', 'situacion', '-situacion'}


def _leer_cantidad(texto):
    try:
        cantidad = Decimal((texto or '').strip().replace(',', '.'))
    except InvalidOperation:
        return None, 'La cantidad debe ser un número válido.'
    if not cantidad.is_finite():
        return None, 'La cantidad debe ser un número válido.'
    if cantidad <= 0:
        return None, 'La cantidad debe ser mayor que cero.'
    if cantidad > MAX_CANTIDAD:
        return None, 'La cantidad supera el máximo permitido.'
    if cantidad.as_tuple().exponent < -3:
        return None, 'La cantidad admite como máximo 3 decimales.'
    return cantidad, None


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def insumo_lista(request):
    insumos = list(Insumo.objects.prefetch_related('productos').order_by('-activo', 'nombre'))
    orden = request.GET.get('orden', '')
    if orden not in ORDENES:
        orden = ''
    if orden:
        campo = orden.lstrip('-')
        if campo == 'nombre':
            clave = lambda i: i.nombre.lower()
        elif campo == 'stock':
            clave = lambda i: i.stock_actual
        else:
            # Situación: qué tan lejos está el stock de su mínimo (stock / mínimo).
            clave = lambda i: i.stock_actual / i.stock_minimo if i.stock_minimo > 0 else Decimal('Infinity')
        insumos.sort(key=clave, reverse=orden.startswith('-'))
        insumos.sort(key=lambda i: not i.activo)  # los dados de baja siempre al final
    alertas = sorted(
        (i for i in insumos if i.activo and i.nivel != 'ok'),
        key=lambda i: (ORDEN_NIVEL[i.nivel], i.nombre.lower()),
    )
    return render(request, 'core/insumo_lista.html', {
        'insumos': insumos,
        'alertas': alertas,
        'hay_activos': any(i.activo for i in insumos),
        'orden': orden,
    })


@permiso_requerido(PERMISO_EDITAR)
@require_http_methods(['GET', 'POST'])
def insumo_crear(request):
    form = InsumoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('insumo_lista')
    return render(request, 'core/insumo_form.html', {'form': form})


@permiso_requerido(PERMISO_EDITAR)
@require_http_methods(['GET', 'POST'])
def insumo_editar(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    form = InsumoForm(request.POST or None, instance=insumo)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('insumo_lista')
    return render(request, 'core/insumo_form.html', {'form': form, 'insumo': insumo})


@permiso_requerido(PERMISO_ESTADO)
@require_http_methods(['POST'])
def insumo_estado(request, pk):
    insumo = get_object_or_404(Insumo, pk=pk)
    insumo.activo = request.POST.get('accion') == 'alta'
    insumo.save(update_fields=['activo'])
    return redirect('insumo_lista')


@permiso_requerido(PERMISO_VER)
@require_http_methods(['GET'])
def insumo_movimientos(request, pk):
    insumo = get_object_or_404(Insumo.objects.prefetch_related('productos'), pk=pk)
    movimientos = insumo.movimientos.select_related('usuario').order_by('-fecha_hora', '-id_movimiento')
    return render(request, 'core/insumo_movimientos.html', {
        'insumo': insumo,
        'movimientos': movimientos,
        'tipos': MovimientoInsumo.TIPOS,
    })


@permiso_requerido(PERMISO_EDITAR)
@require_http_methods(['POST'])
def insumo_movimiento_registrar(request, pk):
    tipo = request.POST.get('tipo', '').strip()
    motivo = request.POST.get('motivo', '').strip()
    cantidad, error = _leer_cantidad(request.POST.get('cantidad'))
    if tipo not in MovimientoInsumo.TIPOS:
        error = 'Elegí si es una entrada o una salida.'
    elif not motivo:
        error = 'Indicá el motivo del movimiento.'
    elif len(motivo) > MAX_TEXTO:
        error = f'El motivo no puede superar {MAX_TEXTO} caracteres.'

    if error is None:
        with transaction.atomic():
            insumo = get_object_or_404(Insumo.objects.select_for_update(), pk=pk)
            if not insumo.activo:
                error = 'El insumo está dado de baja. Dalo de alta para registrar movimientos.'
            elif tipo == MovimientoInsumo.TIPO_SALIDA and cantidad > insumo.stock_actual:
                error = f'No hay suficiente stock: quedan {insumo.stock_actual} {insumo.unidad}.'
            else:
                if tipo == MovimientoInsumo.TIPO_ENTRADA:
                    insumo.stock_actual += cantidad
                else:
                    insumo.stock_actual -= cantidad
                if insumo.stock_actual > MAX_CANTIDAD:
                    error = 'El stock resultante supera el máximo permitido.'
                else:
                    insumo.save(update_fields=['stock_actual'])
                    MovimientoInsumo.objects.create(
                        insumo=insumo,
                        tipo=tipo,
                        cantidad=cantidad,
                        stock_resultante=insumo.stock_actual,
                        fecha_hora=timezone.now(),
                        motivo=motivo,
                        usuario=_usuario_actual(request),
                    )
                    messages.success(request, f'{tipo} de {cantidad} {insumo.unidad} registrada.')

        if error is None and tipo == MovimientoInsumo.TIPO_SALIDA:
            alerta = al_mover_insumo(insumo)
            if alerta is not None:
                messages.warning(request, aviso_para_pantalla(alerta))

    if error:
        messages.error(request, error)
    return redirect('insumo_movimientos', pk=pk)
