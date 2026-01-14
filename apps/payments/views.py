"""
Views для платежей
"""
import uuid
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone

from apps.photos.models import Photo
from apps.payments.models import Purchase, Transaction


@login_required
def create_payment(request, photo_id):
    """Создание платежа для покупки фото"""
    if not request.user.is_client:
        return redirect('accounts:dashboard')
    
    photo = get_object_or_404(Photo, id=photo_id, status='active')
    profile = request.user.client_profile
    
    # Проверяем, не куплено ли уже
    existing = Purchase.objects.filter(
        buyer=profile,
        photo=photo,
        status='paid'
    ).first()
    
    if existing:
        return redirect('clients:photo_detail', pk=photo_id)
    
    # Создаём покупку
    purchase = Purchase.objects.create(
        buyer=profile,
        photo=photo,
        photographer=photo.photographer,
        amount=photo.price,
        download_token=str(uuid.uuid4())
    )
    
    # Здесь интеграция с ЮКассой
    # В реальном проекте:
    # from yookassa import Configuration, Payment
    # Configuration.account_id = settings.YOOKASSA_SHOP_ID
    # Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
    # 
    # payment = Payment.create({
    #     "amount": {"value": str(photo.price), "currency": "RUB"},
    #     "confirmation": {"type": "redirect", "return_url": f"{request.build_absolute_uri('/payments/callback/')}?purchase_id={purchase.id}"},
    #     "capture": True,
    #     "description": f"Покупка фото #{photo.id}"
    # })
    # 
    # purchase.payment_id = payment.id
    # purchase.payment_url = payment.confirmation.confirmation_url
    # purchase.save()
    # return redirect(purchase.payment_url)
    
    # Для демо - сразу помечаем как оплаченное
    purchase.status = 'paid'
    purchase.paid_at = timezone.now()
    purchase.save()
    
    # Обновляем баланс фотографа
    photographer = photo.photographer
    photographer.balance += purchase.photographer_amount
    photographer.total_earned += purchase.photographer_amount
    photographer.save()
    
    # Обновляем статистику клиента
    profile.total_purchases += 1
    profile.total_spent += purchase.amount
    profile.save()
    
    # Создаём транзакции
    Transaction.objects.create(
        user=request.user,
        transaction_type='purchase',
        amount=purchase.amount,
        purchase=purchase,
        description=f"Покупка фото {photo.id}"
    )
    
    Transaction.objects.create(
        user=photographer.user,
        transaction_type='sale',
        amount=purchase.photographer_amount,
        purchase=purchase,
        description=f"Продажа фото {photo.id}"
    )
    
    return redirect('payments:success', purchase_id=purchase.id)


def payment_success(request, purchase_id):
    """Страница успешной оплаты"""
    purchase = get_object_or_404(Purchase, id=purchase_id)
    
    # Проверяем, что это покупка текущего пользователя
    if request.user.is_authenticated and hasattr(request.user, 'client_profile'):
        if purchase.buyer != request.user.client_profile:
            return redirect('clients:dashboard')
    
    return render(request, 'payments/success.html', {'purchase': purchase})


@login_required
def download_photo(request, purchase_id, token):
    """Скачивание оплаченного фото"""
    purchase = get_object_or_404(
        Purchase,
        id=purchase_id,
        download_token=token,
        status='paid'
    )
    
    # Проверяем владельца
    if purchase.buyer.user != request.user:
        return HttpResponse("Доступ запрещён", status=403)
    
    # Проверяем лимит скачиваний
    if purchase.download_count >= purchase.max_downloads:
        return HttpResponse("Превышен лимит скачиваний", status=403)
    
    # Увеличиваем счётчик
    purchase.download_count += 1
    purchase.save()
    
    # Отдаём файл
    photo = purchase.photo
    response = HttpResponse(photo.original.read(), content_type='image/jpeg')
    response['Content-Disposition'] = f'attachment; filename="photo_{photo.id}.jpg"'
    return response


@csrf_exempt
@require_POST
def yookassa_webhook(request):
    """Webhook для уведомлений от ЮКассы"""
    import json
    
    try:
        data = json.loads(request.body)
        event_type = data.get('event')
        
        if event_type == 'payment.succeeded':
            payment_id = data['object']['id']
            
            purchase = Purchase.objects.filter(payment_id=payment_id).first()
            if purchase and purchase.status == 'pending':
                purchase.status = 'paid'
                purchase.paid_at = timezone.now()
                purchase.save()
                
                # Обновляем баланс фотографа
                photographer = purchase.photographer
                photographer.balance += purchase.photographer_amount
                photographer.total_earned += purchase.photographer_amount
                photographer.save()
        
        elif event_type == 'payment.canceled':
            payment_id = data['object']['id']
            purchase = Purchase.objects.filter(payment_id=payment_id).first()
            if purchase:
                purchase.status = 'failed'
                purchase.save()
        
        return JsonResponse({'status': 'ok'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
