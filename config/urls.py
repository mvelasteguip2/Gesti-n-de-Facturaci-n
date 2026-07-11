from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from security.views import InicioTemplate

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', InicioTemplate.as_view(), name='home'),
    path('security/', include('security.urls')),   
    path('catalog/', include('catalog.urls')),     
    path("customers/", include("customers.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
