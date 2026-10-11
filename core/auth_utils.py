from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from .models import Usuario

ROL_ADMIN = 'Administrador'


def _es_api(request):
    return request.path.startswith('/api/')


def _verificar_acceso(request, nombre_permiso=None):
    """Devuelve None si el acceso está permitido, o una respuesta si no."""
    usuario_id = request.session.get('usuario_id')
    usuario = (
        Usuario.objects.select_related('rol').filter(pk=usuario_id).first()
        if usuario_id else None
    )

    
    if usuario is None or not usuario.activo:
        request.session.flush()
        if _es_api(request):
            return JsonResponse({'error': 'Sesión no iniciada'}, status=401)
        return redirect('login_usuario')

    
    if usuario.debe_cambiar_clave:
        if _es_api(request):
            return JsonResponse({'error': 'Debe cambiar su clave temporal'}, status=403)
        return redirect('usuario_cambiar_clave_obligatorio')

    
    if usuario.rol.nombre_rol == ROL_ADMIN:
        return None

    
    if nombre_permiso and not usuario.rol.permisos.filter(nombre_permiso=nombre_permiso).exists():
        if _es_api(request):
            return JsonResponse({'error': 'No tenés permiso para realizar esta acción.'}, status=403)
        messages.error(request, 'No tenés permiso para realizar esta acción.')
        return redirect('dashboard')

    return None


def login_requerido(vista):
    """Solo exige sesión válida (sin permiso específico)."""
    @wraps(vista)
    def envoltorio(request, *args, **kwargs):
        respuesta = _verificar_acceso(request)
        if respuesta is not None:
            return respuesta
        return vista(request, *args, **kwargs)
    return envoltorio


def permiso_requerido(nombre_permiso):
    """Decorador para vistas basadas en función."""
    def decorador(vista):
        @wraps(vista)
        def envoltorio(request, *args, **kwargs):
            respuesta = _verificar_acceso(request, nombre_permiso)
            if respuesta is not None:
                return respuesta
            return vista(request, *args, **kwargs)
        return envoltorio
    return decorador


class LoginRequeridoMixin:
    """Mixin para vistas de clase: solo exige sesión válida."""
    def dispatch(self, request, *args, **kwargs):
        respuesta = _verificar_acceso(request)
        if respuesta is not None:
            return respuesta
        return super().dispatch(request, *args, **kwargs)


class PermisoRequeridoMixin:
    """Mixin para vistas de clase: cada vista define permiso_necesario."""
    permiso_necesario = None

    def dispatch(self, request, *args, **kwargs):
        respuesta = _verificar_acceso(request, self.permiso_necesario)
        if respuesta is not None:
            return respuesta
        return super().dispatch(request, *args, **kwargs)