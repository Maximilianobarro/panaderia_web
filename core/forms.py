from django import forms
from .models import (
    Rol, Categoria,
    Encargo, DetalleEncargo,
    Permiso, Producto,
)
from .views_hito3 import MEDIOS_PAGO


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


class EncargoForm(forms.ModelForm):
    cantidad_items = forms.IntegerField(
        label='Cantidad de ítems',
        min_value=1,
        widget=forms.NumberInput(attrs={'min': 1}),
    )
    medio_pago = forms.ChoiceField(
        label='Medio de pago',
        choices=[('', 'Elegí un medio de pago')] + [(m, m) for m in MEDIOS_PAGO],
    )

    class Meta:
        model = Encargo
        fields = ['fecha_pedido', 'fecha_entrega_prevista', 'senia', 'cantidad_items',
                  'medio_pago', 'observacion', 'usuario', 'cliente']
        labels = {'senia': 'Monto'}
        widgets = {
            'fecha_pedido': forms.DateInput(attrs={'type': 'date'}),
            'fecha_entrega_prevista': forms.DateInput(attrs={'type': 'date'}),
        }


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
        fields = ['nombre', 'descripcion', 'precio_unitario',
                  'stock_actual', 'estado', 'categoria']
