from django import forms
from .models import (
    Rol, Categoria,
    Permiso, Producto, Insumo,
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


class InsumoForm(forms.ModelForm):
    unidad = forms.ChoiceField(choices=[(u, u) for u in Insumo.UNIDADES])
    stock_minimo = forms.DecimalField(
        label='Stock mínimo', min_value=1, max_digits=12, decimal_places=3, initial=0,
        widget=forms.NumberInput(attrs={'min': '1', 'step': '0.001'}),
        error_messages={
            'required': 'Indicá el stock mínimo.',
            'min_value': 'El stock mínimo debe ser 1 o más.',
        },
    )
    productos = forms.ModelMultipleChoiceField(
        queryset=Producto.objects.filter(estado__iexact='activo').order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        label='Productos que lo usan',
        error_messages={'required': 'Marcá al menos un producto que use este insumo.'},
    )

    class Meta:
        model = Insumo
        fields = ['nombre', 'unidad', 'stock_minimo', 'productos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['stock_minimo'] = format(self.instance.stock_minimo.normalize(), 'f')

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        repetidos = Insumo.objects.filter(nombre__iexact=nombre)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError('Ya existe un insumo con ese nombre.')
        return nombre
