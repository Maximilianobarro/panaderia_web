import json
from contextvars import ContextVar

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import post_save, pre_delete, pre_save
from django.utils import timezone

_request_actual = ContextVar('auditoria_request', default=None)

CAMPOS_OCULTOS = {'contrasena_hash'}
CAMPOS_IGNORADOS = {'fecha_ultima_modificacion'}
TEXTO_OCULTO = '(modificada)'


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _request_actual.set(request)
        try:
            return self.get_response(request)
        finally:
            _request_actual.reset(token)


def _usuario_actual_id():
    request = _request_actual.get()
    if request is None:
        return None
    return request.session.get('usuario_id')


def _json(datos):
    return json.dumps(datos, cls=DjangoJSONEncoder, ensure_ascii=False)


def registrar_auditoria(entidad, id_registro, accion, antes=None, despues=None, usuario_id=None):
    from .models import LogAuditoria

    if usuario_id is None:
        usuario_id = _usuario_actual_id()

    LogAuditoria.objects.create(
        fecha_hora=timezone.now(),
        usuario_id=usuario_id,
        entidad=entidad,
        id_registro=id_registro,
        accion=accion,
        valores_anteriores=_json(antes) if antes is not None else None,
        valores_actuales=_json(despues) if despues is not None else None,
    )


def _valores(instancia, campos=None):
    resultado = {}
    for campo in instancia._meta.concrete_fields:
        if campo.primary_key or campo.name in CAMPOS_IGNORADOS:
            continue
        if campos is not None and campo.name not in campos:
            continue
        resultado[campo.attname] = getattr(instancia, campo.attname)
    return resultado


def _iguales(a, b):
    return a == b or str(a) == str(b)


def _ocultar(datos):
    return {k: (TEXTO_OCULTO if k in CAMPOS_OCULTOS else v) for k, v in datos.items()}


def _antes_de_guardar(sender, instance, raw=False, update_fields=None, **kwargs):
    instance._auditoria_previo = None
    if raw or instance.pk is None:
        return
    previo = sender._default_manager.filter(pk=instance.pk).first()
    if previo is not None:
        campos = set(update_fields) if update_fields else None
        instance._auditoria_previo = _valores(previo, campos)


def _despues_de_guardar(sender, instance, created=False, raw=False, update_fields=None, **kwargs):
    previo = getattr(instance, '_auditoria_previo', None)
    instance._auditoria_previo = None
    if created or raw or previo is None:
        return

    campos = set(update_fields) if update_fields else None
    actual = _valores(instance, campos)

    antes, despues = {}, {}
    for nombre, valor in actual.items():
        if nombre in previo and not _iguales(previo[nombre], valor):
            antes[nombre] = previo[nombre]
            despues[nombre] = valor

    if not antes:
        return

    registrar_auditoria(
        sender._meta.db_table,
        instance.pk,
        'MODIFICACION',
        _ocultar(antes),
        _ocultar(despues),
    )


def _antes_de_borrar(sender, instance, **kwargs):
    registrar_auditoria(
        sender._meta.db_table,
        instance.pk,
        'ELIMINACION',
        _ocultar(_valores(instance)),
        None,
    )


def conectar():
    from .models import Categoria, Cliente, DetalleEncargo, Encargo, Permiso, Producto, Rol, Usuario

    for modelo in (Producto, Cliente, Usuario, Categoria, Rol, Permiso, Encargo, DetalleEncargo):
        pre_save.connect(_antes_de_guardar, sender=modelo, dispatch_uid=f'aud_pre_{modelo.__name__}')
        post_save.connect(_despues_de_guardar, sender=modelo, dispatch_uid=f'aud_post_{modelo.__name__}')
        pre_delete.connect(_antes_de_borrar, sender=modelo, dispatch_uid=f'aud_del_{modelo.__name__}')
