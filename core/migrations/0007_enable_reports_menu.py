from django.db import migrations


def enable_reports_menu(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    Permission = apps.get_model('auth', 'Permission')
    permission = Permission.objects.get(
        content_type__app_label='invoicing', codename='view_factura'
    )
    for item in MenuItem.objects.filter(name='Reportes', parent__isnull=False):
        item.url_name = 'invoicing:reports_index'
        item.is_active = True
        item.save(update_fields=['url_name', 'is_active', 'updated_at'])
        item.permissions.set([permission])


def disable_reports_menu(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    for item in MenuItem.objects.filter(name='Reportes', parent__isnull=False):
        item.url_name = ''
        item.is_active = False
        item.save(update_fields=['url_name', 'is_active', 'updated_at'])
        item.permissions.clear()


class Migration(migrations.Migration):
    dependencies = [('core', '0006_configure_menu_permissions')]

    operations = [migrations.RunPython(enable_reports_menu, disable_reports_menu)]
