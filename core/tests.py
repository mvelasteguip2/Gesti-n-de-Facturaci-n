import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalog.models import Categoria, Producto
from customers.models import Cliente
from invoicing.models import Factura
from invoicing.services import FacturaService
from security.models import User


class SmokeTests(TestCase):
    """Pruebas de aceptación básicas de los flujos disponibles hasta el Lab 11."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username='admin',
            first_name='Administrador',
            last_name='Pruebas',
            email='admin@example.com',
            password='ClaveSegura123!',
        )
        cls.categoria = Categoria.objects.create(nombre='General')
        cls.producto = Producto.objects.create(
            codigo='PRD-001',
            nombre='Producto de prueba',
            precio=Decimal('10.00'),
            iva_porcentaje=Decimal('15.00'),
            stock=10,
            stock_minimo=2,
            categoria=cls.categoria,
        )
        cls.cliente = Cliente.objects.create(
            cedula='1234567890',
            nombre='Cliente de prueba',
            email='cliente@example.com',
        )

    def test_login_y_rutas_principales(self):
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, f"{reverse('security:login')}?next=/")

        response = self.client.post(
            reverse('security:login'),
            data=json.dumps({
                'username': self.user.email,
                'password': 'ClaveSegura123!',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['resp'])

        for url_name in (
            'home',
            'security:user_list',
            'security:group_list',
            'security:profile',
            'catalog:categoria_list',
            'catalog:producto_list',
            'customers:cliente_list',
            'invoicing:invoice_list',
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

        dashboard = self.client.get(reverse('home'))
        self.assertContains(dashboard, 'ventasChart')
        self.assertContains(dashboard, 'Productos')
        self.assertNotContains(dashboard, 'Reportes')

    def test_crear_ver_y_anular_factura_restaura_stock(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('invoicing:invoice_create'),
            data={
                'cliente': self.cliente.pk,
                'metodo_pago': 'Efectivo',
                'observaciones': 'Prueba de humo',
                'productos_json': json.dumps([{
                    'producto_id': self.producto.pk,
                    'cantidad': 2,
                    'descuento_pct': '0',
                }]),
            },
        )
        self.assertEqual(response.status_code, 302)

        factura = Factura.objects.get()
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)
        self.assertEqual(factura.subtotal, Decimal('20.00'))
        self.assertEqual(factura.iva_total, Decimal('3.00'))
        self.assertEqual(factura.total, Decimal('23.00'))

        detail = self.client.get(reverse('invoicing:invoice_detail', args=[factura.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, factura.numero)

        annul = self.client.post(reverse('invoicing:invoice_annul', args=[factura.pk]))
        self.assertEqual(annul.status_code, 302)
        factura.refresh_from_db()
        self.producto.refresh_from_db()
        self.assertFalse(factura.is_active)
        self.assertEqual(self.producto.stock, 10)

        second_annul = self.client.post(reverse('invoicing:invoice_annul', args=[factura.pk]))
        self.assertEqual(second_annul.status_code, 302)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_crud_catalogo_y_clientes(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('catalog:categoria_create'), {
            'nombre': 'Accesorios',
            'descripcion': 'Categoría para prueba CRUD',
        })
        self.assertEqual(response.status_code, 302)
        categoria = Categoria.objects.get(nombre='Accesorios')

        response = self.client.post(reverse('catalog:categoria_update', args=[categoria.pk]), {
            'nombre': 'Accesorios Pro',
            'descripcion': 'Categoría actualizada',
        })
        self.assertEqual(response.status_code, 302)
        categoria.refresh_from_db()

        response = self.client.post(reverse('catalog:producto_create'), {
            'codigo': 'PRD-CRUD',
            'nombre': 'Producto CRUD',
            'descripcion': '',
            'precio': '12.50',
            'iva_porcentaje': '15.00',
            'stock': 5,
            'stock_minimo': 1,
            'categoria': categoria.pk,
        })
        self.assertEqual(response.status_code, 302)
        producto = Producto.objects.get(codigo='PRD-CRUD')

        response = self.client.post(reverse('catalog:producto_update', args=[producto.pk]), {
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'descripcion': '',
            'precio': '12.50',
            'iva_porcentaje': '15.00',
            'stock': 7,
            'stock_minimo': 1,
            'categoria': categoria.pk,
        })
        self.assertEqual(response.status_code, 302)
        producto.refresh_from_db()
        self.assertEqual(producto.stock, 7)

        response = self.client.post(reverse('customers:cliente_create'), {
            'cedula': '0987654321',
            'nombre': 'Cliente CRUD',
            'email': 'crud@example.com',
            'telefono': '',
            'direccion': '',
        })
        self.assertEqual(response.status_code, 302)
        cliente = Cliente.objects.get(email='crud@example.com')

        response = self.client.post(reverse('customers:cliente_update', args=[cliente.pk]), {
            'cedula': cliente.cedula,
            'nombre': 'Cliente CRUD editado',
            'email': cliente.email,
            'telefono': '0999999999',
            'direccion': 'Dirección de prueba',
        })
        self.assertEqual(response.status_code, 302)

        self.assertEqual(
            self.client.post(reverse('catalog:producto_deactivate', args=[producto.pk])).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(reverse('catalog:categoria_deactivate', args=[categoria.pk])).status_code,
            302,
        )
        self.assertEqual(
            self.client.post(reverse('customers:cliente_deactivate', args=[cliente.pk])).status_code,
            302,
        )
        categoria.refresh_from_db()
        cliente.refresh_from_db()
        self.assertFalse(categoria.is_active)
        self.assertFalse(cliente.is_active)

    def test_reportes_pdf_y_menu(self):
        self.client.force_login(self.user)
        factura = FacturaService.crear(
            cliente=self.cliente,
            usuario=self.user,
            productos_data=[{
                'producto_id': self.producto.pk,
                'cantidad': 1,
                'descuento_pct': 0,
            }],
        )

        index = self.client.get(reverse('invoicing:reports_index'))
        self.assertEqual(index.status_code, 200)
        self.assertContains(index, 'Cierre del Día')
        self.assertContains(index, 'Listado de Facturas')
        self.assertContains(index, reverse('invoicing:daily_close_pdf'))

        for url in (
            reverse('invoicing:daily_close_pdf'),
            reverse('invoicing:invoice_list_pdf'),
            reverse('invoicing:invoice_pdf', args=[factura.pk]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response['Content-Type'], 'application/pdf')
                self.assertTrue(response.content.startswith(b'%PDF'))

        invalid_dates = self.client.get(
            reverse('invoicing:invoice_list_pdf'),
            {'desde': '2026-07-12', 'hasta': '2026-07-01'},
        )
        self.assertEqual(invalid_dates.status_code, 400)

        dashboard = self.client.get(reverse('home'))
        self.assertContains(dashboard, 'Reportes')
