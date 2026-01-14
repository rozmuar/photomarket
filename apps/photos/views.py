"""
Публичные views для фотографий и событий
"""
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Photo, Event


def photo_gallery(request):
    """Публичная галерея фото"""
    photos = Photo.objects.filter(
        status='active',
        event__is_public=True
    ).select_related('photographer__user', 'event').order_by('-created_at')
    
    paginator = Paginator(photos, 24)
    page = request.GET.get('page')
    photos = paginator.get_page(page)
    
    return render(request, 'photos/gallery.html', {'photos': photos})


def events_list(request):
    """Список публичных событий"""
    events = Event.objects.filter(
        is_public=True
    ).select_related('photographer__user').order_by('-date')
    
    # Фильтры
    event_type = request.GET.get('type')
    city = request.GET.get('city')
    
    if event_type:
        events = events.filter(event_type=event_type)
    if city:
        events = events.filter(city__icontains=city)
    
    paginator = Paginator(events, 12)
    page = request.GET.get('page')
    events = paginator.get_page(page)
    
    return render(request, 'photos/events.html', {
        'events': events,
        'event_types': Event.EventType.choices
    })


def event_detail(request, pk):
    """Детали события"""
    event = get_object_or_404(Event, pk=pk, is_public=True)
    photos = Photo.objects.filter(event=event, status='active').order_by('-created_at')
    
    paginator = Paginator(photos, 24)
    page = request.GET.get('page')
    photos = paginator.get_page(page)
    
    return render(request, 'photos/event_detail.html', {
        'event': event,
        'photos': photos
    })
