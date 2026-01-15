from django.urls import path
from . import views

app_name = 'photographers'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # События
    path('events/', views.EventListView.as_view(), name='events'),
    path('events/create/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
    
    # Фотографии
    path('photos/', views.PhotoListView.as_view(), name='photos'),
    path('photos/upload/', views.photo_upload, name='photo_upload'),
    path('photos/<uuid:pk>/edit/', views.photo_edit, name='photo_edit'),
    path('photos/<uuid:pk>/delete/', views.photo_delete, name='photo_delete'),
    
    # Продажи
    path('sales/', views.SalesListView.as_view(), name='sales'),
    
    # Запросы на удаление
    path('deletion-requests/', views.DeletionRequestListView.as_view(), name='deletion_requests'),
    path('deletion-requests/<int:pk>/', views.process_deletion_request, name='deletion_request_detail'),
    
    # Финансы
    path('withdrawal/', views.withdrawal_request, name='withdrawal'),
]
