from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from .auth_utils import ROL_ADMIN
from .models import CierreCaja, Usuario

PERMISO_CAJA = 'cierre_caja'


def caja_abierta(usuario):
    return CierreCaja.objects.filter(usuario=usuario, estado=CierreCaja.ESTADO_ABIERTA).first()


def usa_caja(usuario):
    if usuario.rol.nombre_rol == ROL_ADMIN:
        return False
    return usuario.rol.permisos.filter(nombre_permiso=PERMISO_CAJA).exists()


def error_sin_caja(usuario):
    if usa_caja(usuario) and caja_abierta(usuario) is None:
        return 'Primero abrí tu caja (Inicio → Caja) para poder registrar cobros o devoluciones.'
    return None


# Pantallas que un empleado puede usar sin tener la caja abierta: Inicio, Caja y el manejo de su sesión.
PANTALLAS_SIN_CAJA = {
    'dashboard',
    'caja_index', 'caja_abrir', 'caja_cerrar', 'caja_lista', 'caja_comprobante',
    'login_usuario', 'logout_usuario', 'usuario_cambiar_clave_obligatorio',
    'recuperar_clave', 'recuperar_clave_nueva',
}
AVISO_SIN_CAJA = 'Primero abrí tu caja para poder usar el sistema.'


class CajaObligatoriaMiddleware:
    """Un empleado que trabaja con caja no puede entrar a otras pantallas sin abrirla.

    Se aplica a los usuarios con el permiso `cierre_caja` que no son Administrador
    (los mismos que abren y cierran caja). Si intentan abrir otra pantalla sin caja
    abierta, se los manda a Caja con un aviso.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        coincidencia = request.resolver_match
        if (coincidencia is None or not coincidencia.url_name or coincidencia.app_name == 'admin'
                or coincidencia.url_name in PANTALLAS_SIN_CAJA):
            return None
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return None
        usuario = Usuario.objects.select_related('rol').filter(pk=usuario_id, activo=True).first()
        if usuario is None or not usa_caja(usuario) or caja_abierta(usuario) is not None:
            return None
        if request.path.startswith('/api/'):
            return JsonResponse({'error': AVISO_SIN_CAJA}, status=403)
        messages.warning(request, AVISO_SIN_CAJA)
        return redirect('caja_index')
