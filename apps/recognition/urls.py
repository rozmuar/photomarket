from django.urls import path
from . import views

app_name = 'recognition'

urlpatterns = [
    path('selfie-status/', views.check_selfie_status, name='selfie_status'),
    path('matched-photos/', views.get_matched_photos, name='matched_photos'),
    path('photo/<uuid:photo_id>/faces/', views.get_photo_faces, name='photo_faces'),
]
