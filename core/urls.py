from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import api_views
from . import generic_views as gv
from . import views_auditoria as aud
from . import views_hito2 as h2
from . import views_hito3 as h3
from . import views_encargos as enc

urlpatterns = [
    path('', RedirectView.as_view(url='/inicio/', permanent=False)),

    # ---------- CLIENTES ----------
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/nuevo/', views.crear_cliente, name='crear_cliente'),
    path('clientes/<int:pk>/editar/', views.editar_cliente, name='editar_cliente'),
    path('clientes/<int:pk>/baja/', views.baja_cliente, name='baja_cliente'),
    path('clientes/<int:pk>/reactivar/', views.reactivar_cliente, name='reactivar_cliente'),
    path('clientes-ajax/', views.clientes_ajax, name='clientes_ajax'),

    path('api/clientes/', api_views.api_lista_clientes, name='api_lista_clientes'),
    path('api/clientes/crear/', api_views.api_crear_cliente, name='api_crear_cliente'),
    path('api/clientes/<int:pk>/editar/', api_views.api_editar_cliente, name='api_editar_cliente'),
    path('api/clientes/<int:pk>/borrar/', api_views.api_borrar_cliente, name='api_borrar_cliente'),

    # ---------- INICIO Y PRODUCTOS ----------
    path('inicio/', views.dashboard, name='dashboard'),
    path('productos/', gv.ProductoListView.as_view(), name='producto_lista'),
    path('productos/nuevo/', gv.ProductoCreateView.as_view(), name='producto_crear'),
    path('productos/<int:pk>/editar/', gv.ProductoUpdateView.as_view(), name='producto_editar'),
    path('productos/<int:pk>/estado/', gv.ProductoEstadoView.as_view(), name='producto_estado'),
    path('productos-ajax/', views.index_view, name='index'),
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/productos/crear/', views.api_crear_producto, name='api_crear_producto'),
    path('api/productos/<int:pk>/editar/', views.api_editar_producto, name='api_editar_producto'),
    path('api/productos/<int:pk>/borrar/', views.api_borrar_producto, name='api_borrar_producto'),
    path('api/categorias/', views.api_categorias, name='api_categorias'),

    # ---------- ROL ----------
    path('roles/', gv.RolListView.as_view(), name='rol_lista'),
    path('roles/nuevo/', gv.RolCreateView.as_view(), name='rol_crear'),
    path('roles/<int:pk>/editar/', gv.RolUpdateView.as_view(), name='rol_editar'),
    path('roles/<int:pk>/estado/', gv.RolEstadoView.as_view(), name='rol_estado'),

    # ---------- CATEGORIA ----------
    path('categorias/', gv.CategoriaListView.as_view(), name='categoria_lista'),
    path('categorias/nueva/', gv.CategoriaCreateView.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', gv.CategoriaUpdateView.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/estado/', gv.CategoriaEstadoView.as_view(), name='categoria_estado'),

    # ---------- USUARIO (Hito Nº2: Alta / Modificación / Baja / Restablecer clave) ----------
    path('usuarios/', h2.usuario_lista, name='usuario_lista'),
    path('usuarios/alta/', h2.usuario_alta, name='usuario_alta'),
    path('usuarios/<int:pk>/modificar/', h2.usuario_modificar, name='usuario_modificar'),
    path('usuarios/<int:pk>/baja/', h2.usuario_baja, name='usuario_baja'),
    path('usuarios/<int:pk>/reactivar/', h2.usuario_reactivar, name='usuario_reactivar'),
    path('usuarios/<int:pk>/restablecer-clave/', h2.usuario_restablecer_clave, name='usuario_restablecer_clave'),

    # ---------- LOGIN / LOGOUT ----------
    path('login/', h2.login_usuario, name='login_usuario'),
    path('logout/', h2.logout_usuario, name='logout_usuario'),
    path('cambiar-clave/', h2.usuario_cambiar_clave_obligatorio, name='usuario_cambiar_clave_obligatorio'),
    path('recuperar-clave/', h2.recuperar_clave, name='recuperar_clave'),
    path('recuperar-clave/nueva/', h2.recuperar_clave_nueva, name='recuperar_clave_nueva'),

    # ---------- PERMISO ----------
    path('permisos/', gv.PermisoListView.as_view(), name='permiso_lista'),
    path('permisos/nuevo/', gv.PermisoCreateView.as_view(), name='permiso_crear'),
    path('permisos/<int:pk>/editar/', gv.PermisoUpdateView.as_view(), name='permiso_editar'),
    path('permisos/<int:pk>/estado/', gv.PermisoEstadoView.as_view(), name='permiso_estado'),

    # ---------- VENTA (Hito Nº3: sin anulación) ----------
    path('ventas/', h3.venta_lista, name='venta_lista'),
    path('ventas/nueva/', h3.venta_crear, name='venta_crear'),
    path('ventas/<int:pk>/', h3.venta_detalle, name='venta_detalle'),
    path('ventas/<int:pk>/comprobante/', h3.venta_comprobante, name='venta_comprobante'),

    # ---------- AUDITORIA (Hito Nº4) ----------
    path('auditoria/', aud.auditoria_lista, name='auditoria_lista'),

    # ---------- ENCARGO (Hito Nº4) ----------
    path('encargos/', enc.encargo_lista, name='encargo_lista'),
    path('encargos/nuevo/', enc.encargo_crear, name='encargo_crear'),
    path('encargos/<int:pk>/', enc.encargo_detalle, name='encargo_detalle'),
    path('encargos/<int:pk>/entregar/', enc.encargo_entregar, name='encargo_entregar'),
    path('encargos/<int:pk>/cancelar/', enc.encargo_cancelar, name='encargo_cancelar'),
    path('encargos/<int:pk>/comprobante/', enc.encargo_comprobante, name='encargo_comprobante'),
    path('detalle-encargos/', enc.produccion_lista, name='detalle_encargo_lista'),
    path('detalle-encargos/<int:pk>/preparado/', enc.encargo_item_preparado, name='encargo_item_preparado'),
]