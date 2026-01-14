"""
URL Configuration для PhotoMarket
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    
    # Главная страница
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Приложения
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('photographer/', include('apps.photographers.urls', namespace='photographers')),
    path('client/', include('apps.clients.urls', namespace='clients')),
    path('photos/', include('apps.photos.urls', namespace='photos')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('api/recognition/', include('apps.recognition.urls', namespace='recognition')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
