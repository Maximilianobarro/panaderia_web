from django.core.management.base import BaseCommand

from core.alertas import enviar_email, revision_diaria


class Command(BaseCommand):
    help = (
        'Revisa las reglas de alertas diarias (stock bajo de insumos y encargos con saldo pendiente). '
        'Pensado para correr una vez por día con el Programador de tareas de Windows.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--probar-email', action='store_true',
            help='Solo envía un correo de prueba al destino configurado, sin revisar las reglas.',
        )

    def handle(self, *args, **options):
        if options['probar_email']:
            ok, detalle = enviar_email(
                'Panadería Zulca - Correo de prueba',
                'Este es un correo de prueba de las alertas del sistema. Si lo recibiste, el envío funciona.',
            )
            estilo = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(estilo(detalle))
            return

        creadas = revision_diaria(forzar=True)
        if not creadas:
            self.stdout.write('Revisión terminada: no hay alertas nuevas.')
            return
        self.stdout.write(self.style.SUCCESS(f'Revisión terminada: {len(creadas)} alerta(s) nueva(s).'))
        for n in creadas:
            self.stdout.write(f'- [{n.tipo}] {n.mensaje}')
