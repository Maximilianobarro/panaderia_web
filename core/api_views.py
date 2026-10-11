import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Cliente


def cliente_a_dict(cliente):
    return {
        'id_cliente': cliente.id_cliente,
        'nombre': cliente.nombre,
        'apellido': cliente.apellido,
        'email': cliente.email,
        'calle': cliente.calle,
        'numero': cliente.numero,
        'ciudad': cliente.ciudad,
        'fecha_alta': cliente.fecha_alta.isoformat() if cliente.fecha_alta else None,
    }


@require_http_methods(["GET"])
def api_lista_clientes(request):
    clientes = Cliente.objects.all().order_by('id_cliente')
    data = [cliente_a_dict(c) for c in clientes]
    return JsonResponse(data, safe=False)


@csrf_exempt
@require_http_methods(["POST"])
def api_crear_cliente(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    if not body.get('nombre') or not body.get('apellido'):
        return JsonResponse({'error': 'nombre y apellido son obligatorios'}, status=400)

    cliente = Cliente.objects.create(
        nombre=body.get('nombre'),
        apellido=body.get('apellido'),
        email=body.get('email', ''),
        calle=body.get('calle', ''),
        numero=body.get('numero', ''),
        ciudad=body.get('ciudad', ''),
    )
    return JsonResponse(cliente_a_dict(cliente), status=201)


@csrf_exempt
@require_http_methods(["PUT"])
def api_editar_cliente(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    cliente.nombre = body.get('nombre', cliente.nombre)
    cliente.apellido = body.get('apellido', cliente.apellido)
    cliente.email = body.get('email', cliente.email)
    cliente.calle = body.get('calle', cliente.calle)
    cliente.numero = body.get('numero', cliente.numero)
    cliente.ciudad = body.get('ciudad', cliente.ciudad)
    cliente.save()
    return JsonResponse(cliente_a_dict(cliente))


@csrf_exempt
@require_http_methods(["DELETE"])
def api_borrar_cliente(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)

    cliente.delete()
    return JsonResponse({'mensaje': 'Cliente eliminado correctamente'})
