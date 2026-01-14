"""
Celery задачи для обработки лиц
"""
from celery import shared_task
from django.db import transaction

from apps.accounts.models import ClientProfile
from apps.photos.models import Photo, PhotoFace
from .services import face_service


@shared_task(bind=True, max_retries=3)
def process_photo_faces(self, photo_id: str):
    """
    Обрабатывает фотографию - находит все лица и сохраняет их кодировки
    """
    try:
        photo = Photo.objects.get(id=photo_id)
        
        # Получаем данные о лицах
        faces_data = face_service.get_face_data(photo.original.path)
        
        with transaction.atomic():
            # Удаляем старые записи о лицах (если есть)
            PhotoFace.objects.filter(photo=photo).delete()
            
            # Создаём новые
            for face_data in faces_data:
                PhotoFace.objects.create(
                    photo=photo,
                    face_location=face_data['location'],
                    face_encoding=face_data['encoding']
                )
            
            # Обновляем статус фото
            photo.faces_count = len(faces_data)
            photo.faces_processed = True
            photo.status = 'active'
            photo.save()
        
        # Запускаем сопоставление с клиентами
        match_faces_with_clients.delay(photo_id)
        
        return f"Обработано {len(faces_data)} лиц на фото {photo_id}"
    
    except Photo.DoesNotExist:
        return f"Фото {photo_id} не найдено"
    except Exception as e:
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def process_client_selfie(self, profile_id: int):
    """
    Обрабатывает селфи клиента - извлекает кодировку лица
    """
    try:
        profile = ClientProfile.objects.get(id=profile_id)
        
        if not profile.selfie:
            profile.face_processing_error = "Селфи не загружено"
            profile.save()
            return "Селфи не найдено"
        
        # Получаем кодировки лиц
        faces_data = face_service.get_face_data(profile.selfie.path)
        
        if not faces_data:
            profile.face_processing_error = "Лицо не обнаружено на фото"
            profile.face_processed = False
            profile.save()
            return "Лицо не найдено"
        
        if len(faces_data) > 1:
            profile.face_processing_error = "На фото обнаружено более одного лица"
            profile.face_processed = False
            profile.save()
            return "Найдено несколько лиц"
        
        # Сохраняем кодировку первого (единственного) лица
        profile.face_encoding = faces_data[0]['encoding']
        profile.face_processed = True
        profile.face_processing_error = ""
        profile.save()
        
        # Запускаем поиск совпадений на всех фото
        find_client_photos.delay(profile_id)
        
        return f"Селфи клиента {profile.user.username} обработано"
    
    except ClientProfile.DoesNotExist:
        return f"Профиль {profile_id} не найден"
    except Exception as e:
        self.retry(exc=e, countdown=60)


@shared_task
def match_faces_with_clients(photo_id: str):
    """
    Сопоставляет лица на фото с зарегистрированными клиентами
    """
    try:
        photo = Photo.objects.get(id=photo_id)
        photo_faces = PhotoFace.objects.filter(photo=photo)
        
        # Получаем всех клиентов с обработанными лицами
        clients = ClientProfile.objects.filter(
            face_processed=True,
            face_encoding__isnull=False
        ).select_related('user')
        
        matches_count = 0
        
        for photo_face in photo_faces:
            for client in clients:
                match, confidence = face_service.compare_faces(
                    client.face_encoding,
                    photo_face.face_encoding
                )
                
                if match:
                    photo_face.matched_user = client.user
                    photo_face.match_confidence = confidence
                    photo_face.save()
                    matches_count += 1
                    break  # Одно лицо = один клиент
        
        return f"Найдено {matches_count} совпадений для фото {photo_id}"
    
    except Photo.DoesNotExist:
        return f"Фото {photo_id} не найдено"


@shared_task
def find_client_photos(profile_id: int):
    """
    Ищет все фото с лицом клиента
    """
    try:
        profile = ClientProfile.objects.get(id=profile_id)
        
        if not profile.face_encoding:
            return "У клиента нет кодировки лица"
        
        # Получаем все необработанные лица на активных фото
        unmatched_faces = PhotoFace.objects.filter(
            matched_user__isnull=True,
            photo__status='active'
        )
        
        matches_count = 0
        
        for face in unmatched_faces:
            match, confidence = face_service.compare_faces(
                profile.face_encoding,
                face.face_encoding
            )
            
            if match:
                face.matched_user = profile.user
                face.match_confidence = confidence
                face.save()
                matches_count += 1
        
        return f"Найдено {matches_count} фото для клиента {profile.user.username}"
    
    except ClientProfile.DoesNotExist:
        return f"Профиль {profile_id} не найден"


@shared_task
def process_all_pending_photos():
    """
    Обрабатывает все фото в статусе processing
    Запускается периодически через Celery Beat
    """
    pending_photos = Photo.objects.filter(
        status='processing',
        faces_processed=False
    )
    
    for photo in pending_photos:
        process_photo_faces.delay(str(photo.id))
    
    return f"Запущена обработка {pending_photos.count()} фото"
