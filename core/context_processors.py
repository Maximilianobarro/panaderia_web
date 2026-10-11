from .auth_utils import ROL_ADMIN
from .models import Usuario


def permisos_usuario(request):
    """Deja es_admin y permisos_usuario disponibles en todos los templates."""
    vacio = {'es_admin': False, 'permisos_usuario': set()}

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return vacio

    usuario = Usuario.objects.select_related('rol').filter(pk=usuario_id).first()
    if usuario is None:
        return vacio

    return {
        'es_admin': usuario.rol.nombre_rol == ROL_ADMIN,
        'permisos_usuario': set(
            usuario.rol.permisos.values_list('nombre_permiso', flat=True)
        ),
    }