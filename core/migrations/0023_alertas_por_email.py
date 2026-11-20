from django.db import migrations


def pasar_a_email(apps, schema_editor):
    """Reemplaza el envío por Telegram por correo electrónico en la configuración.

    Si la 0022 ya se había aplicado con la clave de Telegram, se renombra esa fila
    (conserva las reglas elegidas); si no, se crean las claves de correo.
    """
    Configuracion = apps.get_model('core', 'Configuracion')
    vieja = Configuracion.objects.filter(clave='telegram_reglas').first()
    if vieja is not None and not Configuracion.objects.filter(clave='email_reglas').exists():
        vieja.clave = 'email_reglas'
        vieja.descripcion = 'Reglas que además se envían por correo electrónico (separadas por coma).'
        vieja.save(update_fields=['clave', 'descripcion'])
    Configuracion.objects.get_or_create(
        clave='email_reglas',
        defaults={'valor': 'saldo_pendiente',
                  'descripcion': 'Reglas que además se envían por correo electrónico (separadas por coma).'},
    )
    Configuracion.objects.get_or_create(
        clave='email_destino',
        defaults={'valor': '', 'descripcion': 'Correo electrónico que recibe los avisos de las reglas marcadas.'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_notificaciones_configuracion'),
    ]

    operations = [
        migrations.RunPython(pasar_a_email, migrations.RunPython.noop),
    ]
