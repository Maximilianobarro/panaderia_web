from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .alertas import REGLAS, notificaciones_visibles
from .auth_utils import ROL_ADMIN, login_requerido, permiso_requerido
from .models import Configuracion, Rol
from .views_hito3 import _usuario_actual

FILAS_POR_PAGINA = 30
PERMISO_CONFIGURACION = 'gestionar_configuracion'

# Parámetros que se pueden editar desde la pantalla de configuración.
# tipo: 'entero' (número entero), 'perfil' (nombre de un rol), 'email' (dirección de correo)
# o 'reglas' (lista de reglas).
# Valor que se muestra si el parámetro todavía no está guardado en la tabla configuracion.
VALORES_POR_DEFECTO = {'venta_inusual_unidades': '200'}

PARAMETROS = [
    ('stock_insumo_porcentaje_aviso', 'Stock de insumos: % del stock mínimo para avisar', 'entero', 1, 1000),
    ('perfil_stock_insumo', 'Stock de insumos: perfil que recibe el aviso', 'perfil', None, None),
    ('saldo_dias_aviso', 'Saldos pendientes: días antes de la entrega para avisar', 'entero', 0, 7),
    ('perfil_saldo_pendiente', 'Saldos pendientes: perfil que recibe el aviso', 'perfil', None, None),
    ('venta_inusual_desvios', 'Venta inusual: desvíos estándar sobre el promedio', 'entero', 1, 10),
    ('venta_inusual_minimo_ventas', 'Venta inusual: ventas previas necesarias', 'entero', 2, 100000),
    ('venta_inusual_unidades', 'Venta inusual: unidades a partir de las cuales avisar', 'entero', 1, 100000),
    ('perfil_venta_inusual', 'Venta inusual: perfil que recibe el aviso', 'perfil', None, None),
    ('email_destino', 'Correo que recibe los avisos (vacío = no se envían correos)', 'email', None, None),
    ('email_reglas', 'Reglas que también se envían por correo', 'reglas', None, None),
]


def _es_admin(usuario):
    return usuario.rol.nombre_rol == ROL_ADMIN


@login_requerido
@require_http_methods(['GET'])
def notificacion_lista(request):
    usuario = _usuario_actual(request)
    estado = request.GET.get('estado', 'sin_leer')
    consulta = notificaciones_visibles(usuario, _es_admin(usuario))
    if estado == 'sin_leer':
        consulta = consulta.filter(leida=False)
    elif estado == 'leidas':
        consulta = consulta.filter(leida=True)
    else:
        estado = 'todas'
    pagina = Paginator(consulta.order_by('-fecha', '-id_notificacion'), FILAS_POR_PAGINA).get_page(request.GET.get('page'))
    return render(request, 'core/notificacion_lista.html', {
        'pagina': pagina,
        'paginas': pagina.paginator.get_elided_page_range(pagina.number, on_each_side=2, on_ends=1),
        'estado': estado,
    })


@login_requerido
@require_http_methods(['POST'])
def notificacion_leer(request, pk):
    usuario = _usuario_actual(request)
    notificacion = notificaciones_visibles(usuario, _es_admin(usuario)).filter(pk=pk, leida=False).first()
    if notificacion is not None:
        notificacion.leida = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save(update_fields=['leida', 'fecha_lectura'])
    estado = request.POST.get('estado', 'sin_leer')
    if estado not in ('sin_leer', 'leidas', 'todas'):
        estado = 'sin_leer'
    return redirect(f"{reverse('notificacion_lista')}?estado={estado}")


@login_requerido
@require_http_methods(['POST'])
def notificacion_leer_todas(request):
    usuario = _usuario_actual(request)
    cantidad = notificaciones_visibles(usuario, _es_admin(usuario)).filter(leida=False).update(
        leida=True, fecha_lectura=timezone.now(),
    )
    if cantidad == 1:
        messages.success(request, '1 notificación marcada como leída.')
    else:
        messages.success(request, f'{cantidad} notificaciones marcadas como leídas.')
    return redirect('notificacion_lista')


def _leer_parametro(clave, tipo, minimo, maximo, texto, roles, errores, etiqueta):
    if tipo == 'entero':
        try:
            numero = int(texto)
        except ValueError:
            errores.append(f'«{etiqueta}» debe ser un número entero.')
            return None
        if not (minimo <= numero <= maximo):
            errores.append(f'«{etiqueta}» debe estar entre {minimo} y {maximo}.')
            return None
        return str(numero)
    if tipo == 'email':
        if not texto:
            return ''
        try:
            validate_email(texto)
        except ValidationError:
            errores.append(f'«{etiqueta}»: escribí una dirección de correo válida.')
            return None
        return texto
    if tipo == 'perfil':
        if texto not in roles:
            errores.append(f'«{etiqueta}»: elegí un perfil de la lista.')
            return None
        return texto
    return texto


@permiso_requerido(PERMISO_CONFIGURACION)
@require_http_methods(['GET', 'POST'])
def configuracion_editar(request):
    roles = list(Rol.objects.filter(activo=True).order_by('nombre_rol').values_list('nombre_rol', flat=True))
    actuales = {c.clave: c for c in Configuracion.objects.filter(clave__in=[p[0] for p in PARAMETROS])}
    errores = []
    valores = {clave: (actuales[clave].valor if clave in actuales else VALORES_POR_DEFECTO.get(clave, ''))
               for clave, *_ in PARAMETROS}

    if request.method == 'POST':
        nuevos = {}
        for clave, etiqueta, tipo, minimo, maximo in PARAMETROS:
            if tipo == 'reglas':
                elegidas = [r for r in request.POST.getlist(clave) if r in REGLAS]
                nuevos[clave] = ','.join(elegidas)
            else:
                texto = request.POST.get(clave, '').strip()
                valores[clave] = texto
                nuevos[clave] = _leer_parametro(clave, tipo, minimo, maximo, texto, roles, errores, etiqueta)
        if not errores:
            for clave, valor in nuevos.items():
                fila = actuales.get(clave)
                if fila is None:
                    Configuracion.objects.create(clave=clave, valor=valor)
                elif fila.valor != valor:
                    fila.valor = valor
                    fila.save(update_fields=['valor'])
            messages.success(request, 'Configuración guardada.')
            return redirect('configuracion_editar')

    filas = []
    for clave, etiqueta, tipo, minimo, maximo in PARAMETROS:
        fila = {'clave': clave, 'etiqueta': etiqueta, 'tipo': tipo, 'valor': valores[clave], 'minimo': minimo, 'maximo': maximo}
        if tipo == 'reglas':
            marcadas = {r.strip() for r in valores[clave].split(',')}
            fila['opciones'] = [{'valor': r, 'texto': t, 'marcada': r in marcadas} for r, t in REGLAS.items()]
        filas.append(fila)
    return render(request, 'core/configuracion.html', {'filas': filas, 'roles': roles, 'errores': errores})
