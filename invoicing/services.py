from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from catalog.models import Producto
from .models import DetalleFactura, Factura, SecuenciaFactura


class FacturaService:
    """Logica de negocio transaccional para facturacion."""

    @staticmethod
    @transaction.atomic
    def crear(*, cliente, usuario, productos_data, metodo_pago='Efectivo', observaciones=''):
        if not productos_data:
            raise ValidationError('Debe agregar al menos un producto.')

        year = timezone.now().year
        seq, _ = SecuenciaFactura.objects.select_for_update().get_or_create(year=year)
        seq.correlativo = F('correlativo') + 1
        seq.save(update_fields=['correlativo'])
        seq.refresh_from_db()
        numero = f'FAC-{seq.year}-{seq.correlativo:06d}'

        detalles_data = []
        subtotal_factura = Decimal('0.00')
        iva_factura = Decimal('0.00')

        for item in productos_data:
            producto_id = item.get('producto_id')
            try:
                cantidad = int(item.get('cantidad') or 0)
                descuento_pct = Decimal(str(item.get('descuento_pct', 0) or 0))
            except (TypeError, ValueError, InvalidOperation):
                raise ValidationError('El detalle de productos contiene valores inv\u00e1lidos.')

            try:
                prod = Producto.objects.select_for_update().get(pk=producto_id, is_active=True)
            except Producto.DoesNotExist:
                raise ValidationError('Uno de los productos seleccionados no est\u00e1 disponible.')

            if cantidad <= 0:
                raise ValidationError(f'Cantidad invalida para {prod.nombre}')

            if descuento_pct < 0 or descuento_pct > 100:
                raise ValidationError(f'Descuento invalido para {prod.nombre}')

            if prod.stock < cantidad:
                raise ValidationError(f'Stock insuficiente para {prod.nombre} (disponible: {prod.stock})')

            precio_unitario = prod.precio
            subtotal = Decimal(str(cantidad)) * precio_unitario * (Decimal('1') - descuento_pct / Decimal('100'))
            iva_porcentaje = prod.iva_porcentaje
            iva_valor = subtotal * iva_porcentaje / Decimal('100')
            total = subtotal + iva_valor

            detalles_data.append({
                'producto': prod,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'descuento_pct': descuento_pct,
                'subtotal': subtotal.quantize(Decimal('0.01')),
                'iva_porcentaje': iva_porcentaje,
                'iva_valor': iva_valor.quantize(Decimal('0.01')),
                'total': total.quantize(Decimal('0.01')),
            })

            subtotal_factura += subtotal
            iva_factura += iva_valor

            rows = Producto.objects.filter(pk=prod.pk, stock__gte=cantidad).update(
                stock=F('stock') - cantidad
            )
            if rows == 0:
                raise ValidationError(f'Error al descontar stock de {prod.nombre} (posible condicion de carrera)')

        factura = Factura.objects.create(
            numero=numero,
            cliente=cliente,
            usuario=usuario,
            subtotal=subtotal_factura.quantize(Decimal('0.01')),
            iva_total=iva_factura.quantize(Decimal('0.01')),
            total=(subtotal_factura + iva_factura).quantize(Decimal('0.01')),
            metodo_pago=metodo_pago,
            observaciones=observaciones,
        )

        DetalleFactura.objects.bulk_create([
            DetalleFactura(factura=factura, **detalle) for detalle in detalles_data
        ])

        return factura

    @staticmethod
    @transaction.atomic
    def anular(factura_id):
        factura = Factura.all_objects.select_for_update().get(pk=factura_id)

        if not factura.is_active:
            raise ValidationError('La factura ya esta anulada.')

        for detalle in factura.detalles.select_related('producto').all():
            Producto.objects.filter(pk=detalle.producto_id).update(
                stock=F('stock') + detalle.cantidad
            )

        factura.soft_delete()
        return factura
