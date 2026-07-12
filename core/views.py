import json
from datetime import datetime, time, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views.generic import TemplateView

from catalog.models import Producto
from customers.models import Cliente
from invoicing.models import Factura


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        inicio_mes = hoy.replace(day=1)
        desde = hoy - timedelta(days=6)
        inicio_hoy = timezone.make_aware(datetime.combine(hoy, time.min))
        fin_hoy = inicio_hoy + timedelta(days=1)
        inicio_mes_dt = timezone.make_aware(datetime.combine(inicio_mes, time.min))
        fin_rango = fin_hoy

        facturas_hoy = Factura.objects.filter(
            fecha_emision__gte=inicio_hoy,
            fecha_emision__lt=fin_hoy,
            is_active=True,
        ).aggregate(total=Count('id'))

        ventas_mes = Factura.objects.filter(
            fecha_emision__gte=inicio_mes_dt,
            fecha_emision__lt=fin_rango,
            is_active=True,
        ).aggregate(total=Sum('total'))

        clientes = Cliente.objects.aggregate(total=Count('id'))

        stock_bajo = Producto.objects.filter(
            stock__lte=F('stock_minimo'),
        ).aggregate(total=Count('id'))

        ventas_por_dia = Factura.objects.filter(
            fecha_emision__gte=timezone.make_aware(datetime.combine(desde, time.min)),
            fecha_emision__lt=fin_rango,
            is_active=True,
        ).annotate(
            dia=TruncDate('fecha_emision', tzinfo=timezone.get_current_timezone()),
        ).values('dia').annotate(
            total=Sum('total'),
        ).order_by('dia')

        ventas_map = {venta['dia']: float(venta['total'] or 0) for venta in ventas_por_dia}
        labels = [(desde + timedelta(days=i)).strftime('%d/%m') for i in range(7)]
        data = [ventas_map.get(desde + timedelta(days=i), 0) for i in range(7)]

        context.update({
            'facturas_hoy': facturas_hoy['total'] or 0,
            'ventas_mes': ventas_mes['total'] or 0,
            'total_clientes': clientes['total'] or 0,
            'stock_bajo': stock_bajo['total'] or 0,
            'ultimas_facturas': Factura.objects.select_related('cliente').filter(
                is_active=True,
            ).order_by('-fecha_emision')[:5],
            'chart_labels': json.dumps(labels),
            'chart_data': json.dumps(data),
        })
        return context
