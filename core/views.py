import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Cliente, Producto, Categoria
from .auth_utils import login_requerido, permiso_requerido


# ---------- Clientes ----------
@permiso_requerido('ver_clientes')
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'core/cliente_list.html', {'clientes': clientes})


@permiso_requerido('registrar_cliente')
def crear_cliente(request):
    if request.method == 'POST':
        Cliente.objects.create(
            nombre=request.POST.get('nombre'),
            apellido=request.POST.get('apellido'),
            email=request.POST.get('email'),
            calle=request.POST.get('calle'),
            numero=request.POST.get('numero'),
            ciudad=request.POST.get('ciudad'),
        )
        return redirect('lista_clientes')
    return render(request, 'core/cliente_form.html')


@permiso_requerido('registrar_cliente')
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.nombre = request.POST.get('nombre')
        cliente.apellido = request.POST.get('apellido')
        cliente.email = request.POST.get('email')
        cliente.calle = request.POST.get('calle')
        cliente.numero = request.POST.get('numero')
        cliente.ciudad = request.POST.get('ciudad')
        cliente.save()
        return redirect('lista_clientes')
    return render(request, 'core/cliente_form.html', {'cliente': cliente})


@permiso_requerido('ver_clientes')
def clientes_ajax(request):
    return render(request, 'core/cliente_ajax.html')


@permiso_requerido('registrar_cliente')
def borrar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.delete()
    return redirect('lista_clientes')


# ---------- Paginas ----------
@permiso_requerido('ver_productos')
def index_view(request):
    return render(request, 'core/index.html')


@login_requerido
def dashboard(request):
    return render(request, 'core/dashboard.html')


# ---------- Productos ----------
def producto_a_dict(producto):
    return {
        'id_producto': producto.id_producto,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio_unitario': str(producto.precio_unitario),
        'unidad_medida': producto.unidad_medida,
        'stock_actual': producto.stock_actual,
        'estado': producto.estado,
        'id_categoria': producto.categoria_id,
        'categoria_nombre': producto.categoria.nombre if producto.categoria_id else None,
    }


@permiso_requerido('ver_productos')
@require_http_methods(["GET"])
def api_productos(request):
    productos = Producto.objects.all().order_by('id_producto')
    data = [producto_a_dict(p) for p in productos]
    return JsonResponse(data, safe=False)


@permiso_requerido('ver_productos')
@require_http_methods(["GET"])
def api_categorias(request):
    categorias = Categoria.objects.all().order_by('id_categoria')
    data = [{'id_categoria': c.id_categoria, 'nombre': c.nombre} for c in categorias]
    return JsonResponse(data, safe=False)


@csrf_exempt
@permiso_requerido('editar_stock')
@require_http_methods(["POST"])
def api_crear_producto(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    if not body.get('nombre') or not body.get('precio_unitario') or not body.get('id_categoria'):
        return JsonResponse({'error': 'nombre, precio_unitario y id_categoria son obligatorios'}, status=400)

    try:
        categoria = Categoria.objects.get(pk=body.get('id_categoria'))
    except Categoria.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=400)

    producto = Producto.objects.create(
        nombre=body.get('nombre'),
        descripcion=body.get('descripcion', ''),
        precio_unitario=body.get('precio_unitario'),
        unidad_medida=body.get('unidad_medida', ''),
        stock_actual=body.get('stock_actual', 0),
        estado=body.get('estado', 'activo'),
        categoria=categoria,
    )
    return JsonResponse(producto_a_dict(producto), status=201)


@csrf_exempt
@permiso_requerido('editar_stock')
@require_http_methods(["PUT"])
def api_editar_producto(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    producto.nombre = body.get('nombre', producto.nombre)
    producto.descripcion = body.get('descripcion', producto.descripcion)
    producto.precio_unitario = body.get('precio_unitario', producto.precio_unitario)
    producto.unidad_medida = body.get('unidad_medida', producto.unidad_medida)
    producto.stock_actual = body.get('stock_actual', producto.stock_actual)
    producto.estado = body.get('estado', producto.estado)
    if body.get('id_categoria'):
        try:
            producto.categoria = Categoria.objects.get(pk=body.get('id_categoria'))
        except Categoria.DoesNotExist:
            return JsonResponse({'error': 'Categoría no encontrada'}, status=400)
    producto.save()
    return JsonResponse(producto_a_dict(producto))


@csrf_exempt
@permiso_requerido('editar_stock')
@require_http_methods(["DELETE"])
def api_borrar_producto(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

    producto.delete()
    return JsonResponse({'mensaje': 'Producto eliminado correctamente'})
