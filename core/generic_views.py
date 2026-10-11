from django.urls import reverse_lazy
from .auth_utils import LoginRequeridoMixin, PermisoRequeridoMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import (
    Rol, Categoria,
    Venta, Encargo, DetalleVenta, DetalleEncargo,
    Permiso, Producto, 
)
from .forms import (
    RolForm, CategoriaForm,
    VentaForm, EncargoForm, DetalleVentaForm, DetalleEncargoForm,
    PermisoForm, ProductoForm, 
)


def crud_views(model, form_class, nombre_url, titulo, permiso_ver=None, permiso_editar=None):
    lista_url = f'{nombre_url}_lista'

    class ListV(PermisoRequeridoMixin, ListView):
        pass
    ListV.model = model
    ListV.template_name = 'core/generic_list.html'
    ListV.context_object_name = 'objetos'
    ListV.permiso_necesario = permiso_ver
    ListV.extra_context = {
        'titulo': titulo,
        'crear_url': f'{nombre_url}_crear',
        'editar_url': f'{nombre_url}_editar',
        'borrar_url': f'{nombre_url}_borrar',
    }

    class CreateV(PermisoRequeridoMixin, CreateView):
        pass
    CreateV.model = model
    CreateV.form_class = form_class
    CreateV.template_name = 'core/generic_form.html'
    CreateV.success_url = reverse_lazy(lista_url)
    CreateV.permiso_necesario = permiso_editar
    CreateV.extra_context = {'titulo': titulo, 'volver_url': lista_url}

    class UpdateV(PermisoRequeridoMixin, UpdateView):
        pass
    UpdateV.model = model
    UpdateV.form_class = form_class
    UpdateV.template_name = 'core/generic_form.html'
    UpdateV.success_url = reverse_lazy(lista_url)
    UpdateV.permiso_necesario = permiso_editar
    UpdateV.extra_context = {'titulo': titulo, 'volver_url': lista_url}

    class DeleteV(PermisoRequeridoMixin, DeleteView):
        pass
    DeleteV.model = model
    DeleteV.template_name = 'core/generic_confirm_delete.html'
    DeleteV.success_url = reverse_lazy(lista_url)
    DeleteV.permiso_necesario = permiso_editar
    DeleteV.extra_context = {'volver_url': lista_url}

    return ListV, CreateV, UpdateV, DeleteV


RolListView, RolCreateView, RolUpdateView, RolDeleteView = crud_views(
    Rol, RolForm, 'rol', 'Rol',
    permiso_ver='gestionar_roles', permiso_editar='gestionar_roles'
)
PermisoListView, PermisoCreateView, PermisoUpdateView, PermisoDeleteView = crud_views(
    Permiso, PermisoForm, 'permiso', 'Permiso',
    permiso_ver='gestionar_roles', permiso_editar='gestionar_roles'
)
CategoriaListView, CategoriaCreateView, CategoriaUpdateView, CategoriaDeleteView = crud_views(
    Categoria, CategoriaForm, 'categoria', 'Categoría',
    permiso_ver='ver_categorias', permiso_editar='gestionar_roles'
)
VentaListView, VentaCreateView, VentaUpdateView, VentaDeleteView = crud_views(
    Venta, VentaForm, 'venta', 'Venta',
    permiso_ver='ver_ventas', permiso_editar='registrar_venta'
)
EncargoListView, EncargoCreateView, EncargoUpdateView, EncargoDeleteView = crud_views(
    Encargo, EncargoForm, 'encargo', 'Encargo',
    permiso_ver='ver_ventas', permiso_editar='registrar_venta'
)
DetalleVentaListView, DetalleVentaCreateView, DetalleVentaUpdateView, DetalleVentaDeleteView = crud_views(
    DetalleVenta, DetalleVentaForm, 'detalle_venta', 'Detalle de venta',
    permiso_ver='ver_ventas', permiso_editar='registrar_venta'
)
DetalleEncargoListView, DetalleEncargoCreateView, DetalleEncargoUpdateView, DetalleEncargoDeleteView = crud_views(
    DetalleEncargo, DetalleEncargoForm, 'detalle_encargo', 'Detalle de encargo',
    permiso_ver='ver_ventas', permiso_editar='registrar_venta'
)
ProductoListView, ProductoCreateView, ProductoUpdateView, ProductoDeleteView = crud_views(
    Producto, ProductoForm, 'producto', 'Producto',
    permiso_ver='ver_productos', permiso_editar='editar_stock'
)