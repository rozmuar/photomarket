"""
Кастомные обработчики ошибок и главная страница
"""
from django.shortcuts import render
from django.db.models import Count


def home(request):
    """Главная страница с контекстом"""
    from apps.photos.models import Photo, Event
    from apps.accounts.models import PhotographerProfile
    
    # Последние фото (6 штук)
    latest_photos = Photo.objects.filter(
        status='active'
    ).select_related('photographer__user', 'event').order_by('-created_at')[:6]
    
    # Featured photos для слайдера (первые 5)
    featured_photos = Photo.objects.filter(
        status='active'
    ).select_related('photographer__user').order_by('-created_at')[:5]
    
    # Топ фотографы по количеству фото
    top_photographers = PhotographerProfile.objects.annotate(
        photos_count=Count('photos')
    ).filter(photos_count__gt=0).order_by('-photos_count')[:8]
    
    # Последние события
    latest_events = Event.objects.filter(
        is_public=True
    ).select_related('photographer__user').order_by('-date')[:3]
    
    return render(request, 'home.html', {
        'latest_photos': latest_photos,
        'featured_photos': featured_photos,
        'top_photographers': top_photographers,
        'latest_events': latest_events,
    })


def handler400(request, exception=None):
    """Обработчик ошибки 400 - Некорректный запрос"""
    return render(request, '400.html', status=400)


def handler403(request, exception=None):
    """Обработчик ошибки 403 - Доступ запрещён"""
    return render(request, '403.html', status=403)


def handler404(request, exception=None):
    """Обработчик ошибки 404 - Страница не найдена"""
    return render(request, '404.html', status=404)


def handler500(request):
    """Обработчик ошибки 500 - Внутренняя ошибка сервера"""
    return render(request, '500.html', status=500)
