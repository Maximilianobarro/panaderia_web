from django import forms
from .models import (
    Rol, Categoria,
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


class ProductoForm(forms.ModelForm):
    estado = forms.ChoiceField(
        choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')],
        initial='activo',
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_unitario',
                  'stock_actual', 'estado', 'categoria']
