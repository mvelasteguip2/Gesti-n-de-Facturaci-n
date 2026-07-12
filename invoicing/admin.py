from django.contrib import admin

from .models import DetalleFactura, Factura, SecuenciaFactura


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 0
    readonly_fields = [
        'producto', 'cantidad', 'precio_unitario', 'descuento_pct',
        'subtotal', 'iva_porcentaje', 'iva_valor', 'total',
    ]
    can_delete = False


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'fecha_emision', 'cliente', 'usuario', 'total', 'metodo_pago', 'is_active']
    list_filter = ['is_active', 'metodo_pago', 'fecha_emision']
    search_fields = ['numero', 'cliente__nombre', 'cliente__cedula', 'usuario__email']
    readonly_fields = ['numero', 'fecha_emision', 'subtotal', 'iva_total', 'total']
    inlines = [DetalleFacturaInline]

    def get_queryset(self, request):
        return Factura.all_objects.select_related('cliente', 'usuario')


@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ['factura', 'producto', 'cantidad', 'precio_unitario', 'subtotal', 'iva_valor', 'total']
    search_fields = ['factura__numero', 'producto__nombre', 'producto__codigo']


@admin.register(SecuenciaFactura)
class SecuenciaFacturaAdmin(admin.ModelAdmin):
    list_display = ['year', 'correlativo']
