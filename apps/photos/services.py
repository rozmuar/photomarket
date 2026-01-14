"""
Сервис обработки фотографий
- Создание превью (thumbnail)
- Добавление водяных знаков
- Распознавание лиц
"""
import os
import uuid
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from django.core.files.base import ContentFile
from django.conf import settings


class PhotoProcessingService:
    """Сервис обработки фотографий"""
    
    def __init__(self):
        self.thumbnail_size = getattr(settings, 'THUMBNAIL_SIZE', (400, 400))
        self.watermark_text = getattr(settings, 'WATERMARK_TEXT', 'PhotoMarket')
        self.watermark_opacity = getattr(settings, 'WATERMARK_OPACITY', 0.5)
    
    def process_photo(self, photo):
        """
        Полная обработка фото:
        1. Создание превью
        2. Создание версии с водяным знаком
        3. Распознавание лиц
        4. Обновление статуса
        """
        try:
            # Открываем оригинал
            img = Image.open(photo.original.path)
            
            # 1. Создаём превью
            self.create_thumbnail(photo, img)
            
            # 2. Создаём версию с водяным знаком
            self.create_watermarked(photo, img)
            
            # 3. Распознавание лиц
            faces_count = self.detect_faces(photo)
            photo.faces_count = faces_count
            
            # 4. Обновляем статус
            photo.status = 'active'
            photo.save()
            
            return True
        except Exception as e:
            print(f"Ошибка обработки фото {photo.id}: {e}")
            photo.status = 'error'
            photo.save()
            return False
    
    def create_thumbnail(self, photo, img=None):
        """Создание превью"""
        if img is None:
            img = Image.open(photo.original.path)
        
        # Копируем и уменьшаем
        thumb = img.copy()
        thumb.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
        
        # Сохраняем в BytesIO
        buffer = BytesIO()
        
        # Определяем формат
        format = 'JPEG' if img.mode == 'RGB' else 'PNG'
        if img.mode == 'RGBA':
            format = 'PNG'
        elif img.mode != 'RGB':
            thumb = thumb.convert('RGB')
            format = 'JPEG'
        
        thumb.save(buffer, format=format, quality=85)
        buffer.seek(0)
        
        # Генерируем имя файла
        ext = 'jpg' if format == 'JPEG' else 'png'
        filename = f"{uuid.uuid4()}.{ext}"
        
        # Сохраняем в поле модели
        photo.thumbnail.save(filename, ContentFile(buffer.read()), save=False)
    
    def create_watermarked(self, photo, img=None):
        """Создание версии с водяным знаком"""
        if img is None:
            img = Image.open(photo.original.path)
        
        # Конвертируем в RGBA для прозрачности
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        watermarked = img.copy()
        
        # Создаём слой для водяного знака
        txt_layer = Image.new('RGBA', watermarked.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Размер шрифта зависит от размера изображения
        font_size = max(30, min(watermarked.width, watermarked.height) // 15)
        
        try:
            # Пробуем загрузить шрифт
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Текст водяного знака
        text = self.watermark_text
        
        # Получаем размер текста
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Размещаем водяные знаки по диагонали
        opacity = int(255 * self.watermark_opacity)
        
        # Шаг между водяными знаками
        step_x = text_width + 100
        step_y = text_height + 100
        
        for y in range(-watermarked.height, watermarked.height * 2, step_y):
            for x in range(-watermarked.width, watermarked.width * 2, step_x):
                # Рисуем текст с небольшим поворотом
                draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
        
        # Поворачиваем слой с водяными знаками
        txt_layer = txt_layer.rotate(-30, expand=False, center=(watermarked.width // 2, watermarked.height // 2))
        
        # Накладываем водяной знак
        watermarked = Image.alpha_composite(watermarked, txt_layer)
        
        # Конвертируем обратно в RGB для JPEG
        watermarked = watermarked.convert('RGB')
        
        # Уменьшаем качество для защиты
        buffer = BytesIO()
        watermarked.save(buffer, format='JPEG', quality=70)
        buffer.seek(0)
        
        # Сохраняем
        filename = f"{uuid.uuid4()}.jpg"
        photo.watermarked.save(filename, ContentFile(buffer.read()), save=False)
    
    def detect_faces(self, photo):
        """Распознавание лиц на фото и сопоставление с клиентами"""
        try:
            from apps.recognition.services import face_service
            
            if not face_service.available:
                print("[INFO] face_recognition недоступен, пропускаем распознавание")
                return 0
            
            # Получаем данные о лицах
            faces = face_service.get_face_data(photo.original.path)
            
            # Загружаем клиентов с обработанными селфи
            from apps.accounts.models import ClientProfile
            from apps.photos.models import PhotoFace
            
            clients_with_faces = list(ClientProfile.objects.filter(
                face_processed=True
            ).exclude(face_encoding__isnull=True).select_related('user'))
            
            # Сохраняем каждое лицо в базу и пробуем сопоставить
            for face in faces:
                photo_face = PhotoFace.objects.create(
                    photo=photo,
                    face_location=face['location'],
                    face_encoding=face['encoding']
                )
                
                # Пробуем найти совпадение среди клиентов
                for client in clients_with_faces:
                    if client.face_encoding:
                        is_match, confidence = face_service.compare_faces(
                            client.face_encoding,
                            face['encoding']
                        )
                        if is_match:
                            photo_face.matched_user = client.user
                            photo_face.save()
                            print(f"[MATCH] Найдено совпадение: фото {photo.id} -> пользователь {client.user.username}")
                            break  # Один пользователь на одно лицо
            
            return len(faces)
        except Exception as e:
            print(f"Ошибка распознавания лиц: {e}")
            return 0


# Синглтон
photo_service = PhotoProcessingService()
