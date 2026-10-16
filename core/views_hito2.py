import re
import time
import unicodedata
import secrets
import string

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


def generar_clave_temporal(largo=10):
    alfabeto = ''.join(c for c in string.ascii_letters if c not in 'lIO') + '23456789'
    while True:
        clave = ''.join(secrets.choice(alfabeto) for _ in range(largo))
        if any(c.islower() for c in clave) and any(c.isupper() for c in clave) and any(c.isdigit() for c in clave):
            return clave


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

        errores = []
        if not dni.isdecimal():
            errores.append('El DNI debe ser numérico.')
        elif Usuario.objects.filter(dni=dni).exists():
            errores.append('Ya existe un usuario con ese DNI.')
        if not apellido:
            errores.append('El apellido es obligatorio.')