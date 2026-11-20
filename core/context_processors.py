from .auth_utils import ROL_ADMIN
from .models import Notificacion, Usuario


def permisos_usuario(request):
    """Deja es_admin y permisos_usuario disponibles en todos los templates."""
    vacio = {'es_admin': False, 'permisos_usuario': set(), 'notificaciones_sin_leer': 0}

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return vacio

    usuario = Usuario.objects.select_related('rol').filter(pk=usuario_id).first()
    if usuario is None:
        return vacio

    es_admin = usuario.rol.nombre_rol == ROL_ADMIN
    sin_leer = Notificacion.objects.filter(leida=False)
    if not es_admin:
        sin_leer = sin_leer.filter(destino_perfil__iexact=usuario.rol.nombre_rol)

    return {
        'es_admin': es_admin,
        'permisos_usuario': set(
            usuario.rol.permisos.values_list('nombre_permiso', flat=True)
        ),
        'notificaciones_sin_leer': sin_leer.count(),
    }