from django.db import migrations


def update_invoicing_menu_urls(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    MenuItem.objects.filter(name__in=['Facturas', 'Reportes'], parent__isnull=False).update(
        url_name='invoicing:invoice_list'
    )


def reverse_invoicing_menu_urls(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    MenuItem.objects.filter(name__in=['Facturas', 'Reportes'], parent__isnull=False).update(
        url_name=''
    )


class Migration(migrations.Migration):
    dependencies = [('core', '0003_update_menu_urls')]

    operations = [migrations.RunPython(update_invoicing_menu_urls, reverse_invoicing_menu_urls)]
