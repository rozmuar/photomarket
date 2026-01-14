"""
API для распознавания лиц
"""
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json

from apps.accounts.models import ClientProfile
from apps.photos.models import Photo, PhotoFace
from .services import face_service


@login_required
@require_GET
def check_selfie_status(request):
    """
    Проверка статуса обработки селфи
    """
    if not request.user.is_client:
        return JsonResponse({'error': 'Доступно только для клиентов'}, status=403)
    
    try:
        profile = request.user.client_profile
        return JsonResponse({
            'processed': profile.face_processed,
            'has_selfie': bool(profile.selfie),
            'error': profile.face_processing_error or None
        })
    except ClientProfile.DoesNotExist:
        return JsonResponse({'error': 'Профиль не найден'}, status=404)


@login_required
@require_GET
def get_matched_photos(request):
    """
    Получение списка фото, где найдено лицо пользователя
    """
    if not request.user.is_client:
        return JsonResponse({'error': 'Доступно только для клиентов'}, status=403)
    
    try:
        profile = request.user.client_profile
        
        if not profile.face_processed:
            return JsonResponse({
                'status': 'not_processed',
                'message': 'Сначала загрузите селфи'
            })
        
        matched_faces = PhotoFace.objects.filter(
            matched_user=request.user
        ).select_related('photo', 'photo__event', 'photo__photographer__user')
        
        photos = []
        for face in matched_faces:
            photo = face.photo
            photos.append({
                'id': str(photo.id),
                'thumbnail': photo.thumbnail.url if photo.thumbnail else photo.watermarked.url if photo.watermarked else None,
                'price': float(photo.price),
                'event': photo.event.name if photo.event else None,
                'photographer': photo.photographer.user.get_full_name() or photo.photographer.user.username,
                'confidence': face.match_confidence,
                'created_at': photo.created_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(photos),
            'photos': photos
        })
    
    except ClientProfile.DoesNotExist:
        return JsonResponse({'error': 'Профиль не найден'}, status=404)


@login_required
@require_GET 
def get_photo_faces(request, photo_id):
    """
    Получение информации о лицах на фото (для фотографа)
    """
    if not request.user.is_photographer:
        return JsonResponse({'error': 'Доступно только для фотографов'}, status=403)
    
    try:
        photo = Photo.objects.get(
            id=photo_id,
            photographer=request.user.photographer_profile
        )
        
        faces = PhotoFace.objects.filter(photo=photo).select_related('matched_user')
        
        faces_data = []
        for face in faces:
            faces_data.append({
                'id': face.id,
                'location': face.face_location,
                'matched_user': face.matched_user.username if face.matched_user else None,
                'confidence': face.match_confidence
            })
        
        return JsonResponse({
            'photo_id': str(photo.id),
            'faces_count': len(faces_data),
            'faces': faces_data
        })
    
    except Photo.DoesNotExist:
        return JsonResponse({'error': 'Фото не найдено'}, status=404)
