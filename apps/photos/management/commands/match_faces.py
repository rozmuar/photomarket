"""
Команда для сопоставления лиц на фото с клиентами
"""
from django.core.management.base import BaseCommand
from apps.photos.models import PhotoFace
from apps.accounts.models import ClientProfile
from apps.recognition.services import face_service


class Command(BaseCommand):
    help = 'Сопоставляет лица на фото с селфи клиентов'

    def handle(self, *args, **options):
        if not face_service.available:
            self.stdout.write(self.style.ERROR('face_recognition недоступен!'))
            return
        
        # Получаем клиентов с обработанными селфи
        clients = list(ClientProfile.objects.filter(
            face_processed=True
        ).exclude(face_encoding__isnull=True).select_related('user'))
        
        self.stdout.write(f'Клиентов с селфи: {len(clients)}')
        
        if not clients:
            self.stdout.write(self.style.WARNING('Нет клиентов с обработанными селфи'))
            return
        
        # Получаем все лица без сопоставления
        unmatched_faces = PhotoFace.objects.filter(
            matched_user__isnull=True
        ).exclude(face_encoding__isnull=True)
        
        self.stdout.write(f'Несопоставленных лиц: {unmatched_faces.count()}')
        
        matched_count = 0
        
        for photo_face in unmatched_faces:
            for client in clients:
                if client.face_encoding and photo_face.face_encoding:
                    is_match, confidence = face_service.compare_faces(
                        client.face_encoding,
                        photo_face.face_encoding
                    )
                    if is_match:
                        photo_face.matched_user = client.user
                        photo_face.save()
                        matched_count += 1
                        self.stdout.write(
                            f'  Фото {photo_face.photo_id} -> {client.user.username} ({confidence:.1f}%)'
                        )
                        break
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Сопоставлено лиц: {matched_count}'))
