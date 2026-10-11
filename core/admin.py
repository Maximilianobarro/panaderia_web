from django.contrib import admin
from .models import (
    Rol, Categoria, Cliente, Usuario, Producto,
    Venta, Encargo, DetalleVenta, DetalleEncargo
)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nombre_rol', 'descripcion')
    search_fields = ('nombre_rol',)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id_categoria', 'nombre', 'descripcion')
    search_fields = ('nombre',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id_cliente', 'nombre', 'apellido', 'email', 'ciudad')
    search_fields = ('nombre', 'apellido', 'email')


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nombre_usuario', 'nombre', 'apellido', 'email', 'rol')
    search_fields = ('nombre_usuario', 'nombre', 'apellido', 'email')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('id_producto', 'nombre', 'precio_unitario', 'stock_actual', 'categoria')
    search_fields = ('nombre',)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id_venta', 'fecha_hora', 'medio_pago', 'estado', 'cliente', 'usuario')
    list_filter = ('estado', 'medio_pago')


@admin.register(Encargo)
class EncargoAdmin(admin.ModelAdmin):
    list_display = ('id_encargo', 'fecha_pedido', 'fecha_entrega_prevista', 'senia', 'estado', 'cliente')
    list_filter = ('estado',)


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario_venta', 'subtotal')


@admin.register(DetalleEncargo)
class DetalleEncargoAdmin(admin.ModelAdmin):
    list_display = ('encargo', 'producto', 'cantidad', 'precio_unitario', 'subtotal')