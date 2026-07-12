from django.db import migrations


MENU_PERMISSIONS = {
    'Usuarios': 'security.view_user',
    'Roles': 'auth.view_group',
    'Categorías': 'catalog.view_categoria',
    'Productos': 'catalog.view_producto',
    'Listado de Clientes': 'customers.view_cliente',
    'Facturas': 'invoicing.view_factura',
}

MENU_URLS = {
    'Usuarios': 'security:user_list',
    'Roles': 'security:group_list',
    'Categorías': 'catalog:categoria_list',
    'Productos': 'catalog:producto_list',
    'Listado de Clientes': 'customers:cliente_list',
    'Facturas': 'invoicing:invoice_list',
}


def configure_menu_permissions(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    for name, permission_name in MENU_PERMISSIONS.items():
        app_label, codename = permission_name.split('.')
        content_type, _ = ContentType.objects.get_or_create(
            app_label=app_label,
            model=codename.removeprefix('view_'),
        )
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={'name': f'Can view {content_type.model}'},
        )
        MenuItem.objects.filter(name=name, parent__isnull=False).update(
            url_name=MENU_URLS[name]
        )
        for item in MenuItem.objects.filter(name=name, parent__isnull=False):
            item.permissions.set([permission])

    MenuItem.objects.filter(name='Reportes', parent__isnull=False).update(is_active=False)


def reverse_configure_menu_permissions(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    MenuItem.objects.filter(name__in=MENU_PERMISSIONS, parent__isnull=False).update(url_name='')
    for item in MenuItem.objects.filter(name__in=MENU_PERMISSIONS, parent__isnull=False):
        item.permissions.clear()
    MenuItem.objects.filter(name='Reportes', parent__isnull=False).update(is_active=True)


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('catalog', '0001_initial'),
        ('core', '0005_update_invoicing_menu_urls'),
        ('customers', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('invoicing', '0001_initial'),
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(configure_menu_permissions, reverse_configure_menu_permissions),
    ]
