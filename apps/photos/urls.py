from django.urls import path
from . import views

app_name = 'photos'

urlpatterns = [
    # Публичные страницы
    path('', views.photo_gallery, name='gallery'),
    path('events/', views.events_list, name='events'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
]
