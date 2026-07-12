from datetime import datetime, time, timedelta
from io import BytesIO

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.staticfiles import finders
from django.db.models import Count, Sum
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from xhtml2pdf import pisa

from .models import Factura


class PDFMixin:
    pdf_template = None
    pdf_filename = 'reporte.pdf'

    def render_pdf(self, context):
        html = render_to_string(self.pdf_template, context, request=self.request)
        result = BytesIO()
        pdf = pisa.pisaDocument(
            BytesIO(html.encode('UTF-8')),
            dest=result,
            encoding='UTF-8',
            link_callback=self._link_callback,
        )
        if pdf.err:
            return HttpResponse('No fue posible generar el PDF.', status=500)

        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self.pdf_filename}"'
        return response

    @staticmethod
    def _link_callback(uri, rel):
        """Resuelve recursos estáticos para xhtml2pdf sin duplicar settings."""
        return finders.find(uri.removeprefix('/static/')) or uri


class ReportsIndexView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = 'invoicing.view_factura'
    template_name = 'invoicing/reports/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.localdate()
        return context


class DailyClosePDFView(LoginRequiredMixin, PermissionRequiredMixin, PDFMixin, View):
    permission_required = 'invoicing.view_factura'
    pdf_template = 'invoicing/reports/daily_close_pdf.html'

    def get(self, request):
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today, time.min))
        end = start + timedelta(days=1)
        self.pdf_filename = f'cierre_diario_{today:%Y%m%d}.pdf'

        invoices = Factura.all_objects.filter(
            fecha_emision__gte=start,
            fecha_emision__lt=end,
        ).select_related('cliente').order_by('fecha_emision')
        active_invoices = invoices.filter(is_active=True)

        return self.render_pdf({
            'fecha': today,
            'facturas': invoices,
            'resumen': active_invoices.aggregate(
                total=Sum('total'), subtotal=Sum('subtotal'),
                iva=Sum('iva_total'), cantidad=Count('id'),
            ),
            'por_metodo': list(active_invoices.values('metodo_pago').annotate(
                total=Sum('total'), cantidad=Count('id'),
            ).order_by('metodo_pago')),
            'anuladas': invoices.filter(is_active=False).count(),
        })


class InvoiceListPDFView(LoginRequiredMixin, PermissionRequiredMixin, PDFMixin, View):
    permission_required = 'invoicing.view_factura'
    pdf_template = 'invoicing/reports/invoice_list_pdf.html'

    def get(self, request):
        try:
            start_date, end_date = self._get_date_range(request)
        except ValueError:
            return HttpResponseBadRequest('Las fechas del reporte no son válidas.')

        start = timezone.make_aware(datetime.combine(start_date, time.min))
        end = timezone.make_aware(datetime.combine(end_date, time.min)) + timedelta(days=1)
        self.pdf_filename = f'facturas_{start_date:%Y%m%d}_al_{end_date:%Y%m%d}.pdf'

        invoices = Factura.all_objects.filter(
            fecha_emision__gte=start,
            fecha_emision__lt=end,
        ).select_related('cliente').order_by('-fecha_emision')
        active_invoices = invoices.filter(is_active=True)

        return self.render_pdf({
            'facturas': invoices,
            'resumen': active_invoices.aggregate(
                total=Sum('total'), subtotal=Sum('subtotal'),
                iva=Sum('iva_total'), cantidad=Count('id'),
            ),
            'anuladas': invoices.filter(is_active=False).count(),
            'desde': start_date,
            'hasta': end_date,
        })

    @staticmethod
    def _get_date_range(request):
        today = timezone.localdate()
        raw_start = request.GET.get('desde')
        raw_end = request.GET.get('hasta')
        start = datetime.strptime(raw_start, '%Y-%m-%d').date() if raw_start else today.replace(day=1)
        end = datetime.strptime(raw_end, '%Y-%m-%d').date() if raw_end else today
        if start > end:
            raise ValueError
        return start, end


class InvoicePDFView(LoginRequiredMixin, PermissionRequiredMixin, PDFMixin, View):
    permission_required = 'invoicing.view_factura'
    pdf_template = 'invoicing/reports/invoice_pdf.html'

    def get(self, request, pk):
        invoice = get_object_or_404(
            Factura.all_objects.select_related('cliente', 'usuario').prefetch_related(
                'detalles__producto'
            ),
            pk=pk,
        )
        self.pdf_filename = f'{invoice.numero}.pdf'
        return self.render_pdf({'factura': invoice, 'detalles': invoice.detalles.all()})
