from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload-selfie/', views.upload_selfie, name='upload_selfie'),
    path('search-photos/', views.search_photos, name='search_photos'),
    path('my-photos/', views.MyPhotosView.as_view(), name='my_photos'),
    path('photo/<uuid:pk>/', views.PhotoDetailView.as_view(), name='photo_detail'),
    path('photo/<uuid:photo_id>/request-deletion/', views.request_deletion, name='request_deletion'),
    path('purchases/', views.PurchasesView.as_view(), name='purchases'),
    path('deletion-requests/', views.DeletionRequestsView.as_view(), name='deletion_requests'),
]
