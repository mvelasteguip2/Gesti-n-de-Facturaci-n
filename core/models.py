from django.contrib.auth.models import Permission
from django.db import models
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    def get_queryset(self):
        return super().get_queryset().active()

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    class Meta:
        abstract = True
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])
    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.save(update_fields=['is_active', 'deleted_at', 'updated_at'])

class MenuItem(BaseModel):
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='Módulo padre')
    name = models.CharField('Nombre', max_length=100)
    icon = models.CharField('Icono', max_length=50, blank=True)
    url_name = models.CharField('URL interna', max_length=200, blank=True)
    order = models.PositiveIntegerField('Orden', default=0)
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name='Permisos requeridos')
    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Elemento de menú'
        verbose_name_plural = 'Elementos del menú'
    def __str__(self): return self.name
    @property
    def is_module(self): return self.parent is None
    @property
    def is_submodule(self): return self.parent is not None
    def _check_permissions(self, user):
        if not self.permissions.exists(): return True
        return user.has_perms([f'{p.content_type.app_label}.{p.codename}' for p in self.permissions.select_related('content_type').only('codename', 'content_type__app_label')])
    def has_access(self, user):
        if not self.is_active: return False
        if self.is_module:
            children = MenuItem.all_objects.filter(parent=self, is_active=True)
            if children.exists(): return any(child.has_access(user) for child in children)
        return self._check_permissions(user)
    def accessible_children(self, user):
        if not self.is_module: return MenuItem.objects.none()
        children = MenuItem.all_objects.filter(parent=self, is_active=True).order_by('order')
        return [child for child in children if child.has_access(user)]
