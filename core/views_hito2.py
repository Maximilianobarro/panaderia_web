import re
import time
import unicodedata

from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .auth_utils import permiso_requerido, ROL_ADMIN
from .models import Usuario, Rol

PERMISO_USUARIOS = 'gestionar_usuarios'
LARGO_MIN_CLAVE = 8
MAX_INTENTOS_RECUPERO = 5
MINUTOS_RECUPERO = 10


def _limpiar(texto):
    """Minúsculas, sin tildes y solo letras/números."""
    nfkd = unicodedata.normalize('NFKD', texto)
    sin_tildes = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]', '', sin_tildes.lower())


def _email_valido(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def _roles_asignables():
    """El Administrador es único: no se puede asignar a otras personas."""
    return Rol.objects.exclude(nombre_rol__iexact=ROL_ADMIN)


def _es_administrador(usuario):
    return usuario.rol.nombre_rol.strip().lower() == ROL_ADMIN.lower()


def _clave_valida(clave):
    return len(clave) >= LARGO_MIN_CLAVE and bool(clave.strip())


def generar_nombre_usuario(apellido, nombre):
    base = _limpiar(apellido) + _limpiar(nombre)[:1] or 'usuario'
    candidato = base
    contador = 1
    while Usuario.objects.filter(nombre_usuario=candidato).exists():
        contador += 1
        candidato = f"{base}{contador}"
    return candidato


@permiso_requerido(PERMISO_USUARIOS)
@require_http_methods(["GET", "POST"])
def usuario_alta(request):
    roles = _roles_asignables()

    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        rol_id = request.POST.get('rol', '')
        activo = request.POST.get('activo') == 'on'
        clave = request.POST.get('clave_inicial', '')

        errores = []
        if not dni.isdecimal():
            errores.append('El DNI debe ser numérico.')
        elif Usuario.objects.filter(dni=dni).exists():
            errores.append('Ya existe un usuario con ese DNI.')
        if not apellido:
            errores.append('El apellido es obligatorio.')
        if not nombre:
            errores.append('El nombre es obligatorio.')
        if not email:
            errores.append('El correo es obligatorio.')
        elif not _email_valido(email):
            errores.append('El correo no es válido.')
        if not _clave_valida(clave):
            errores.append(f'La contraseña debe tener al menos {LARGO_MIN_CLAVE} caracteres.')

        rol = roles.filter(pk=rol_id).first() if rol_id.isdecimal() else None
        if rol is None:
            errores.append('Debe seleccionar un perfil (rol) válido.')

        if errores:
            return render(request, 'core/usuario_alta.html', {
                'errores': errores,
                'roles': roles,
                'datos': request.POST,
            })

        usuario = Usuario.objects.create(
            dni=dni,
            apellido=apellido,
            nombre=nombre,
            email=email,
            nombre_usuario=generar_nombre_usuario(apellido, nombre),
            contrasena_hash=make_password(clave),
            activo=activo,
            debe_cambiar_clave=False,
            rol=rol,
        )

        return render(request, 'core/usuario_alta_exito.html', {
            'usuario': usuario,
            'clave': clave,
        })

    return render(request, 'core/usuario_alta.html', {'roles': roles})


@permiso_requerido(PERMISO_USUARIOS)
@require_http_methods(["GET", "POST"])
def usuario_modificar(request, pk):
    usuario = get_object_or_404(Usuario.objects.select_related('rol'), pk=pk)
    roles = _roles_asignables()
    es_administrador = _es_administrador(usuario)
    error = None

    if request.method == 'POST':
        nuevo_email = request.POST.get('email', '').strip()
        rol_id = request.POST.get('rol', '')

        if not _email_valido(nuevo_email):
            error = 'El correo no es válido.'
        else:
            usuario.email = nuevo_email
            if rol_id.isdecimal() and not es_administrador:
                nuevo_rol = roles.filter(pk=rol_id).first()
                if nuevo_rol:
                    usuario.rol = nuevo_rol
            usuario.save()
            return redirect('usuario_lista')

    return render(request, 'core/usuario_modificar.html', {
        'usuario': usuario,
        'roles': roles,
        'es_administrador': es_administrador,
        'error': error,
    })


@permiso_requerido(PERMISO_USUARIOS)
@require_http_methods(["GET", "POST"])
def usuario_baja(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if usuario.pk == request.session.get('usuario_id'):
        messages.error(request, 'No podés darte de baja a vos mismo.')
        return redirect('usuario_lista')

    if request.method == 'POST':
        usuario.activo = False
        usuario.fecha_baja = timezone.localdate()
        usuario.save()
        return redirect('usuario_lista')

    return render(request, 'core/usuario_baja_confirm.html', {'usuario': usuario})


@permiso_requerido(PERMISO_USUARIOS)
@require_http_methods(["GET", "POST"])
def usuario_restablecer_clave(request, pk):
    usuario = get_object_or_404(Usuario.objects.select_related('rol'), pk=pk)
    error = None

    if request.method == 'POST':
        clave = request.POST.get('clave', '')
        if not _clave_valida(clave):
            error = f'La contraseña debe tener al menos {LARGO_MIN_CLAVE} caracteres.'
        else:
            usuario.contrasena_hash = make_password(clave)
            usuario.debe_cambiar_clave = False
            usuario.save()
            return render(request, 'core/usuario_alta_exito.html', {
                'usuario': usuario,
                'clave': clave,
                'es_restablecimiento': True,
            })

    return render(request, 'core/usuario_restablecer_clave.html', {
        'usuario': usuario,
        'error': error,
    })


@permiso_requerido(PERMISO_USUARIOS)
def usuario_lista(request):
    usuarios = Usuario.objects.select_related('rol').order_by('id_usuario')
    return render(request, 'core/usuario_list.html', {'usuarios': usuarios})


@require_http_methods(["GET", "POST"])
def login_usuario(request):
    error = None
    if request.method == 'POST':
        nombre_usuario = request.POST.get('nombre_usuario', '').strip()
        clave = request.POST.get('clave', '')

        usuario = Usuario.objects.filter(nombre_usuario=nombre_usuario).first()

        if usuario and check_password(clave, usuario.contrasena_hash):
            if not usuario.activo:
                error = 'El usuario está dado de baja.'
            else:
                request.session.cycle_key()
                request.session['usuario_id'] = usuario.id_usuario
                request.session['nombre_usuario'] = usuario.nombre_usuario
                if usuario.debe_cambiar_clave:
                    return redirect('usuario_cambiar_clave_obligatorio')
                return redirect('dashboard')
        else:
            error = 'Usuario o clave incorrectos.'

    return render(request, 'core/login.html', {'error': error})


@require_http_methods(["GET", "POST"])
def usuario_cambiar_clave_obligatorio(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login_usuario')

    usuario = Usuario.objects.filter(pk=usuario_id, activo=True).first()
    if usuario is None:
        request.session.flush()
        return redirect('login_usuario')

    error = None
    if request.method == 'POST':
        clave_nueva = request.POST.get('clave_nueva', '')
        clave_confirmar = request.POST.get('clave_confirmar', '')

        if clave_nueva != clave_confirmar:
            error = 'Las claves no coinciden.'
        elif len(clave_nueva) < LARGO_MIN_CLAVE:
            error = f'La clave debe tener al menos {LARGO_MIN_CLAVE} caracteres.'
        elif check_password(clave_nueva, usuario.contrasena_hash):
            error = 'La nueva clave debe ser distinta de la anterior.'
        else:
            usuario.contrasena_hash = make_password(clave_nueva)
            usuario.debe_cambiar_clave = False
            usuario.save()
            return redirect('dashboard')

    return render(request, 'core/usuario_cambiar_clave.html', {'error': error})


def logout_usuario(request):
    request.session.flush()
    return redirect('login_usuario')


@require_http_methods(["GET", "POST"])
def recuperar_clave(request):
    """Paso 1: el usuario se identifica con usuario + DNI + correo."""
    error = None
    if request.method == 'POST':
        nombre_usuario = request.POST.get('nombre_usuario', '').strip()
        dni = request.POST.get('dni', '').strip()
        email = request.POST.get('email', '').strip()

        clave_cache = f'recuperar:{nombre_usuario.lower()}'
        intentos = cache.get(clave_cache, 0)

        if intentos >= MAX_INTENTOS_RECUPERO:
            error = 'Demasiados intentos. Probá de nuevo en 15 minutos.'
        else:
            usuario = None
            if dni.isdecimal() and len(dni) <= 10:
                usuario = Usuario.objects.filter(
                    nombre_usuario=nombre_usuario,
                    dni=dni,
                    email__iexact=email,
                    activo=True,
                ).first()

            if usuario:
                cache.delete(clave_cache)
                request.session.cycle_key()
                request.session['recuperar_usuario_id'] = usuario.id_usuario
                request.session['recuperar_hasta'] = time.time() + MINUTOS_RECUPERO * 60
                return redirect('recuperar_clave_nueva')

            cache.set(clave_cache, intentos + 1, 900)
            error = 'Los datos no coinciden con ningún usuario activo.'

    return render(request, 'core/recuperar_clave.html', {'error': error})


@require_http_methods(["GET", "POST"])
def recuperar_clave_nueva(request):
    """Paso 2: elegir y confirmar la contraseña nueva."""
    usuario_id = request.session.get('recuperar_usuario_id')
    vence = request.session.get('recuperar_hasta', 0)

    if not usuario_id or time.time() > vence:
        request.session.pop('recuperar_usuario_id', None)
        request.session.pop('recuperar_hasta', None)
        messages.error(request, 'La recuperación venció. Empezá de nuevo.')
        return redirect('recuperar_clave')

    usuario = Usuario.objects.filter(pk=usuario_id, activo=True).first()
    if usuario is None:
        return redirect('recuperar_clave')

    error = None
    if request.method == 'POST':
        clave_nueva = request.POST.get('clave_nueva', '')
        clave_confirmar = request.POST.get('clave_confirmar', '')

        if clave_nueva != clave_confirmar:
            error = 'Las claves no coinciden.'
        elif len(clave_nueva) < LARGO_MIN_CLAVE:
            error = f'La clave debe tener al menos {LARGO_MIN_CLAVE} caracteres.'
        elif check_password(clave_nueva, usuario.contrasena_hash):
            error = 'La nueva clave debe ser distinta de la anterior.'
        else:
            usuario.contrasena_hash = make_password(clave_nueva)
            usuario.debe_cambiar_clave = False
            usuario.save()
            request.session.pop('recuperar_usuario_id', None)
            request.session.pop('recuperar_hasta', None)
            messages.success(request, 'Contraseña actualizada. Ya podés ingresar.')
            return redirect('login_usuario')

    return render(request, 'core/recuperar_clave_nueva.html', {
        'error': error,
        'usuario': usuario,
    })