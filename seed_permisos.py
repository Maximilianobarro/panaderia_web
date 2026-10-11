from core.models import Rol, Permiso, RolPermiso

PERMISOS = {
    'ver_productos': 'Ver productos y stock',
    'editar_stock': 'Crear, editar y borrar productos',
    'ver_ventas': 'Ver ventas, encargos y sus detalles',
    'registrar_venta': 'Registrar y modificar ventas y encargos',
    'ver_clientes': 'Ver clientes',
    'registrar_cliente': 'Alta, edición y baja de clientes',
    'ver_categorias': 'Ver categorías',
    'gestionar_roles': 'Administrar roles y permisos',
    'gestionar_usuarios': 'Alta, baja y restablecimiento de usuarios',
}

ROLES = {
    'Administrador': list(PERMISOS),
    'Cajero': ['ver_productos', 'ver_ventas', 'registrar_venta', 'ver_clientes', 'registrar_cliente'],
    'Maestro Panadero': ['ver_productos', 'editar_stock', 'ver_categorias'],
}

for nombre, descripcion in PERMISOS.items():
    if not Permiso.objects.filter(nombre_permiso=nombre).exists():
        Permiso.objects.create(nombre_permiso=nombre, descripcion=descripcion)

for nombre_rol, lista in ROLES.items():
    rol = Rol.objects.filter(nombre_rol__iexact=nombre_rol).first()
    if rol is None:
        print('NO existe el rol:', nombre_rol)
        continue
    for permiso in Permiso.objects.filter(nombre_permiso__in=lista):
        RolPermiso.objects.get_or_create(rol=rol, permiso=permiso)
    print(rol.nombre_rol, '->', sorted(rol.permisos.values_list('nombre_permiso', flat=True)))