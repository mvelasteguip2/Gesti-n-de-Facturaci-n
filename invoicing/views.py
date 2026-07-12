import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from catalog.models import Producto
from customers.models import Cliente
from .forms import FacturaForm
from .models import Factura
from .services import FacturaService


class InvoiceListView(PermissionRequiredMixin, ListView):
    permission_required = 'invoicing.view_factura'
    model = Factura
    paginate_by = 10
    template_name = 'invoicing/invoice_list.html'

    def get_queryset(self):
        qs = Factura.all_objects.select_related('cliente', 'usuario').all()
        fdesde = self.request.GET.get('desde', '').strip()
        fhasta = self.request.GET.get('hasta', '').strip()
        cliente_id = self.request.GET.get('cliente', '').strip()
        if fdesde:
            qs = qs.filter(fecha_emision__date__gte=fdesde)
        if fhasta:
            qs = qs.filter(fecha_emision__date__lte=fhasta)
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        return qs.order_by('-fecha_emision')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.filter(is_active=True).order_by('nombre')
        return context


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'invoicing.add_factura'
    template_name = 'invoicing/invoice_form.html'

    def get(self, request):
        form = FacturaForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = FacturaForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        try:
            productos_data = json.loads(request.POST.get('productos_json', '[]'))
            factura = FacturaService.crear(
                cliente=form.cleaned_data['cliente'],
                usuario=request.user,
                productos_data=productos_data,
                metodo_pago=form.cleaned_data['metodo_pago'],
                observaciones=form.cleaned_data['observaciones'],
            )
            messages.success(request, f'Factura {factura.numero} creada correctamente.')
            return redirect('invoicing:invoice_detail', pk=factura.pk)
        except (json.JSONDecodeError, TypeError):
            messages.error(request, 'Detalle de productos invalido.')
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        except Exception as exc:
            messages.error(request, str(exc))
        return render(request, self.template_name, {'form': form})


class InvoiceDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'invoicing.view_factura'
    model = Factura
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'factura'

    def get_queryset(self):
        return Factura.all_objects.select_related('cliente', 'usuario').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['detalles'] = self.object.detalles.select_related('producto').all()
        return context


class InvoiceAnnulView(PermissionRequiredMixin, View):
    permission_required = 'invoicing.delete_factura'

    def post(self, request, pk):
        try:
            factura = FacturaService.anular(pk)
            messages.success(request, f'Factura {factura.numero} anulada. Stock restaurado.')
        except ValidationError as exc:
            messages.error(request, '; '.join(exc.messages))
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('invoicing:invoice_list')


@login_required
def api_productos(request):
    q = request.GET.get('q', '').strip()
    qs = Producto.objects.filter(is_active=True, stock__gt=0)
    if q:
        qs = qs.filter(models.Q(nombre__icontains=q) | models.Q(codigo__icontains=q))
    data = list(qs.values('id', 'codigo', 'nombre', 'precio', 'iva_porcentaje', 'stock')[:20])
    return JsonResponse(data, safe=False)


@login_required
def api_clientes(request):
    q = request.GET.get('q', '').strip()
    qs = Cliente.objects.filter(is_active=True)
    if q:
        qs = qs.filter(
            models.Q(nombre__icontains=q) |
            models.Q(cedula__icontains=q) |
            models.Q(email__icontains=q)
        )
    data = list(qs.values('id', 'cedula', 'nombre', 'email')[:20])
    return JsonResponse(data, safe=False)
