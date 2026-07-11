from django.db import migrations


def update_menu_urls(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    url_names = {
        'Usuarios': 'security:user_list',
        'Roles': 'security:group_list',
        'Categor\u00edas': 'catalog:categoria_list',
        'Productos': 'catalog:producto_list',
    }
    for name, url_name in url_names.items():
        MenuItem.objects.filter(name=name, parent__isnull=False).update(url_name=url_name)


def reverse_update_menu_urls(apps, schema_editor):
    MenuItem = apps.get_model('core', 'MenuItem')
    MenuItem.objects.filter(
        name__in=['Usuarios', 'Roles', 'Categor\u00edas', 'Productos'],
        parent__isnull=False,
    ).update(url_name='')


class Migration(migrations.Migration):
    dependencies = [('core', '0002_seed_menu')]

    operations = [migrations.RunPython(update_menu_urls, reverse_update_menu_urls)]
