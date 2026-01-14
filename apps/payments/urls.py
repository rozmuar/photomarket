from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('buy/<uuid:photo_id>/', views.create_payment, name='create_payment'),
    path('success/<uuid:purchase_id>/', views.payment_success, name='success'),
    path('download/<uuid:purchase_id>/<str:token>/', views.download_photo, name='download'),
    path('webhook/yookassa/', views.yookassa_webhook, name='yookassa_webhook'),
]
