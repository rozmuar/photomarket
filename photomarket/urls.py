"""
URL Configuration для PhotoMarket
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    
    # Главная страница
    path('', views.home, name='home'),
    
    # Статические страницы
    path('license/', views.license_view, name='license'),
    path('privacy/', views.privacy_view, name='privacy'),
    
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

# Кастомные страницы ошибок
handler400 = 'photomarket.views.handler400'
handler403 = 'photomarket.views.handler403'
handler404 = 'photomarket.views.handler404'
handler500 = 'photomarket.views.handler500'
