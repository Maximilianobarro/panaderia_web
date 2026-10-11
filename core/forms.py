from django import forms
from .models import (
    Rol, Categoria,
    Venta, Encargo, DetalleVenta, DetalleEncargo,
    Permiso, Producto, 
)


class RolForm(forms.ModelForm):
    permisos = forms.ModelMultipleChoiceField(
        queryset=Permiso.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Rol
        fields = ['nombre_rol', 'descripcion', 'permisos']


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']


class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['nombre_permiso', 'descripcion']


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['fecha_hora', 'medio_pago', 'estado', 'usuario', 'cliente']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class EncargoForm(forms.ModelForm):
    class Meta:
        model = Encargo
        fields = ['fecha_pedido', 'fecha_entrega_prevista', 'senia', 'estado',
                  'observacion', 'usuario', 'cliente']
        widgets = {
            'fecha_pedido': forms.DateInput(attrs={'type': 'date'}),
            'fecha_entrega_prevista': forms.DateInput(attrs={'type': 'date'}),
        }


class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['venta', 'producto', 'cantidad', 'precio_unitario_venta', 'subtotal']


class DetalleEncargoForm(forms.ModelForm):
    class Meta:
        model = DetalleEncargo
        fields = ['encargo', 'producto', 'cantidad', 'precio_unitario', 'subtotal']

class ProductoForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        initial='activo',
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_unitario', 'unidad_medida',
                  'stock_actual', 'estado', 'categoria']
