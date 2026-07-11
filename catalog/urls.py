from django.urls import path
from .views import (
    CategoriaListView, CategoriaCreateView, CategoriaUpdateView,
    ProductoListView, ProductoCreateView, ProductoUpdateView
)

app_name = 'catalog'

urlpatterns = [
    path('categorias/', CategoriaListView.as_view(), name='categoria_list'),
    path('categories/', CategoriaListView.as_view()),
    path('categorias/nuevo/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('categories/new/', CategoriaCreateView.as_view()),
    path('categorias/editar/<int:pk>/', CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categories/edit/<int:pk>/', CategoriaUpdateView.as_view()),

    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('products/', ProductoListView.as_view()),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('products/new/', ProductoCreateView.as_view()),
    path('productos/editar/<int:pk>/', ProductoUpdateView.as_view(), name='producto_update'),
    path('products/edit/<int:pk>/', ProductoUpdateView.as_view()),
    path('productos/desactivar/<int:pk>/', ProductoUpdateView.as_view(), name='producto_deactivate'),
    path('products/deactivate/<int:pk>/', ProductoUpdateView.as_view()),
]