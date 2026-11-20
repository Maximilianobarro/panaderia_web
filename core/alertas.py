"""Módulo de notificaciones y alertas (Parcial Nº 2, M3).

Cada regla revisa una condición sobre los datos y, si se cumple, crea una
notificación en la tabla `notificacion`. Los umbrales se leen de la tabla
`configuracion`; ninguno está escrito en el código.

Para que una misma situación no se notifique dos veces, antes de crear una
notificación se busca otra de la misma regla y el mismo registro que siga sin
leer o que se haya creado hoy. La búsqueda y la creación se hacen dentro de
una transacción que bloquea la fila de configuración de la regla, así dos
pedidos simultáneos no pueden crear la misma notificación.
"""
import logging
import os
import smtplib
import ssl
from datetime import datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage

from django.db import transaction
from django.db.models import Avg, Count, StdDev
from django.utils import timezone

from .models import Configuracion, Encargo, Insumo, Notificacion, Venta
from .views_hito3 import ESTADO_CONFIRMADA, ZONA_LOCAL, _hoy

logger = logging.getLogger(__name__)

REGLA_STOCK = 'stock_insumo'
REGLA_SALDO = 'saldo_pendiente'
REGLA_VENTA = 'venta_inusual'

REGLAS = {
    REGLA_STOCK: 'Stock bajo de insumo',
    REGLA_SALDO: 'Saldo pendiente de encargo',
    REGLA_VENTA: 'Venta de monto inusual',
}

CLAVE_ULTIMA_REVISION = 'ultima_revision_diaria'


# ---------- Configuración ----------

def valor_config(clave, defecto=''):
    fila = Configuracion.objects.filter(clave=clave).first()
    return fila.valor if fila is not None else defecto


def numero_config(clave, defecto):
    try:
        return Decimal(valor_config(clave, str(defecto)))
    except InvalidOperation:
        return Decimal(defecto)


def reglas_email():
    texto = valor_config('email_reglas', '')
    return {r.strip() for r in texto.split(',') if r.strip()}


# ---------- Correo electrónico (SMTP) ----------

def enviar_email(asunto, texto):
    """Envía un correo por SMTP al destino configurado. Devuelve (ok, detalle).

    La cuenta que envía se toma de las variables de entorno EMAIL_USUARIO y
    EMAIL_CLAVE (en Gmail, una contraseña de aplicación). Servidor por defecto:
    smtp.gmail.com, puerto 587 con STARTTLS (se cambia con EMAIL_HOST y EMAIL_PORT).
    """
    destino = valor_config('email_destino', '').strip()
    usuario = os.environ.get('EMAIL_USUARIO', '').strip()
    clave = os.environ.get('EMAIL_CLAVE', '').replace(' ', '')
    if not destino:
        return False, 'No hay un correo de destino cargado en Configuración de alertas.'
    if not usuario or not clave:
        return False, 'Faltan las variables de entorno EMAIL_USUARIO y EMAIL_CLAVE.'

    mensaje = EmailMessage()
    mensaje['Subject'] = asunto
    mensaje['From'] = f'Panadería Zulca <{usuario}>'
    mensaje['To'] = destino
    mensaje.set_content(texto)

    servidor = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    puerto = int(os.environ.get('EMAIL_PORT', '587'))
    try:
        with smtplib.SMTP(servidor, puerto, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(usuario, clave)
            smtp.send_message(mensaje)
    except smtplib.SMTPAuthenticationError:
        return False, 'El servidor de correo rechazó el usuario o la contraseña de aplicación.'
    except Exception as error:  # sin conexión, puerto bloqueado, etc.
        return False, f'No se pudo enviar el correo: {error}'
    return True, f'Correo enviado a {destino}.'


def _texto_email(notificacion):
    momento = timezone.localtime(notificacion.fecha)
    return (
        f'{notificacion.mensaje}\n\n'
        f'Tipo de alerta: {notificacion.tipo}\n'
        f'Fecha y hora: {momento:%d/%m/%Y %H:%M}\n'
        f'Perfil destinatario: {notificacion.destino_perfil}\n\n'
        'Podés verla y marcarla como leída en el sistema, en Notificaciones.\n'
        '-- Panadería Zulca (mensaje automático)'
    )


# ---------- Creación sin duplicados ----------

def _inicio_hoy():
    return datetime.combine(_hoy(), time.min, tzinfo=ZONA_LOCAL)


def notificar(regla, entidad, id_registro, mensaje):
    """Crea la notificación si no existe otra igual sin leer o creada hoy.

    Devuelve la notificación creada, o None si ya existía.
    """
    with transaction.atomic():
        # Bloquea la fila de la regla: serializa la verificación y la creación.
        Configuracion.objects.select_for_update().filter(clave=f'perfil_{regla}').first()
        misma = Notificacion.objects.filter(regla=regla, entidad=entidad, id_registro=id_registro)
        if misma.filter(leida=False).exists() or misma.filter(fecha__gte=_inicio_hoy()).exists():
            return None
        notificacion = Notificacion.objects.create(
            fecha=timezone.now(),
            tipo=REGLAS[regla],
            mensaje=mensaje[:300],
            destino_perfil=valor_config(f'perfil_{regla}', 'Administrador') or 'Administrador',
            regla=regla,
            entidad=entidad,
            id_registro=id_registro,
        )
    if regla in reglas_email():
        ok, detalle = enviar_email(f'Panadería Zulca - {notificacion.tipo}', _texto_email(notificacion))
        if not ok:
            logger.warning(detalle)
    return notificacion


def _seguro(funcion, *args):
    """Ejecuta una regla sin que un error en la alerta afecte la operación principal."""
    try:
        return funcion(*args)
    except Exception:
        logger.exception('Error al evaluar una regla de alerta')
        return None


# ---------- Regla 1: stock bajo de insumo ----------

def _texto_cantidad(valor):
    return f'{valor.normalize():f}' if isinstance(valor, Decimal) else str(valor)


def revisar_stock_insumo(insumo):
    porcentaje = numero_config('stock_insumo_porcentaje_aviso', 100)
    if not insumo.activo or insumo.stock_minimo <= 0:
        return None
    limite = insumo.stock_minimo * porcentaje / 100
    if insumo.stock_actual > limite:
        return None
    mensaje = (
        f'El insumo «{insumo.nombre}» tiene {_texto_cantidad(insumo.stock_actual)} {insumo.unidad} '
        f'(stock mínimo {_texto_cantidad(insumo.stock_minimo)} {insumo.unidad}). Hay que reponerlo.'
    )
    return notificar(REGLA_STOCK, 'insumo', insumo.pk, mensaje)


def revisar_stock_insumos():
    return [n for n in (revisar_stock_insumo(i) for i in Insumo.objects.filter(activo=True)) if n]


# ---------- Regla 2: encargo con saldo pendiente cerca de la entrega ----------

def _cuando(fecha_entrega, hoy):
    dias = (fecha_entrega - hoy).days
    if dias < 0:
        return f'debía entregarse el {fecha_entrega:%d/%m/%Y} (hace {-dias} día{"s" if dias < -1 else ""})'
    if dias == 0:
        return 'se entrega hoy'
    if dias == 1:
        return 'se entrega mañana'
    return f'se entrega el {fecha_entrega:%d/%m/%Y} (en {dias} días)'


def revisar_saldo_encargo(encargo):
    dias = int(numero_config('saldo_dias_aviso', 1))
    hoy = _hoy()
    if encargo.estado != Encargo.ESTADO_PENDIENTE or encargo.saldo_pagado:
        return None
    if encargo.fecha_entrega_prevista is None or encargo.fecha_entrega_prevista > hoy + timedelta(days=dias):
        return None
    mensaje = (
        f'El encargo {encargo.numero_comprobante} de {encargo.cliente} '
        f'{_cuando(encargo.fecha_entrega_prevista, hoy)} y tiene un saldo sin cobrar de ${encargo.saldo:.2f}.'
    )
    return notificar(REGLA_SALDO, 'encargo', encargo.pk, mensaje)


def revisar_saldos_pendientes():
    encargos = Encargo.objects.filter(
        estado=Encargo.ESTADO_PENDIENTE, fecha_pago_saldo__isnull=True,
    ).select_related('cliente')
    return [n for n in (revisar_saldo_encargo(e) for e in encargos) if n]


# ---------- Regla 3: venta de monto inusual ----------

def revisar_venta_inusual(venta):
    desvios = numero_config('venta_inusual_desvios', 3)
    minimo = int(numero_config('venta_inusual_minimo_ventas', 30))
    previas = Venta.objects.filter(estado=ESTADO_CONFIRMADA).exclude(pk=venta.pk)
    datos = previas.aggregate(cantidad=Count('pk'), promedio=Avg('total'), desvio=StdDev('total', sample=True))
    if datos['cantidad'] < minimo or not datos['desvio']:
        return None
    promedio = Decimal(str(datos['promedio']))
    desvio = Decimal(str(datos['desvio']))
    limite = promedio + desvios * desvio
    if venta.total <= limite:
        return None
    mensaje = (
        f'La venta {venta.numero_comprobante} por ${venta.total:.2f} supera el límite de ${limite:.2f} '
        f'(promedio ${promedio:.2f} + {_texto_cantidad(desvios)} desvíos de ${desvio:.2f}). '
        f'Registró: {venta.usuario}.'
    )
    return notificar(REGLA_VENTA, 'venta', venta.pk, mensaje)


# ---------- Puntos de entrada ----------

def al_registrar_venta(venta):
    return _seguro(revisar_venta_inusual, venta)


def al_registrar_encargo(encargo):
    return _seguro(revisar_saldo_encargo, encargo)


def al_mover_insumo(insumo):
    return _seguro(revisar_stock_insumo, insumo)


def revision_diaria(forzar=False):
    """Revisa las reglas de stock y saldos. Sin `forzar`, corre como mucho una vez por día.

    Devuelve la lista de notificaciones creadas, o None si hoy ya se había revisado.
    """
    hoy = _hoy().isoformat()
    with transaction.atomic():
        fila, _ = Configuracion.objects.select_for_update().get_or_create(
            clave=CLAVE_ULTIMA_REVISION,
            defaults={'descripcion': 'Fecha de la última revisión diaria automática (la completa el sistema).'},
        )
        if fila.valor == hoy and not forzar:
            return None
        fila.valor = hoy
        fila.save(update_fields=['valor'])
    return revisar_stock_insumos() + revisar_saldos_pendientes()


def revision_diaria_segura():
    return _seguro(revision_diaria)


# ---------- Bandeja ----------

def notificaciones_visibles(usuario, es_admin):
    consulta = Notificacion.objects.all()
    if not es_admin:
        consulta = consulta.filter(destino_perfil__iexact=usuario.rol.nombre_rol)
    return consulta
