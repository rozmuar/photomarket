"""
Модели фотографий и событий
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from apps.accounts.models import User, PhotographerProfile


def photo_upload_path(instance, filename):
    """Генерация пути для загрузки фото"""
    ext = filename.split('.')[-1]
    return f"photos/{instance.photographer.user.id}/{instance.event.id if instance.event else 'no_event'}/{uuid.uuid4()}.{ext}"


def watermarked_upload_path(instance, filename):
    """Путь для фото с водяным знаком"""
    ext = filename.split('.')[-1]
    return f"watermarked/{instance.photographer.user.id}/{uuid.uuid4()}.{ext}"


def thumbnail_upload_path(instance, filename):
    """Путь для превью"""
    ext = filename.split('.')[-1]
    return f"thumbnails/{instance.photographer.user.id}/{uuid.uuid4()}.{ext}"


class Event(models.Model):
    """
    Событие/Мероприятие (марафон, свадьба, концерт и т.д.)
    """
    class EventType(models.TextChoices):
        WEDDING = 'wedding', 'Свадьба'
        SPORT = 'sport', 'Спортивное мероприятие'
        CONCERT = 'concert', 'Концерт'
        CORPORATE = 'corporate', 'Корпоратив'
        PARTY = 'party', 'Вечеринка'
        GRADUATION = 'graduation', 'Выпускной'
        CHILDREN = 'children', 'Детский праздник'
        OTHER = 'other', 'Другое'
    
    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Фотограф'
    )
    
    name = models.CharField(max_length=300, verbose_name='Название события')
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER,
        verbose_name='Тип события'
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Место и время
    location = models.CharField(max_length=500, blank=True, verbose_name='Место проведения')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    date = models.DateField(verbose_name='Дата события')
    
    # Настройки
    default_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена за фото по умолчанию'
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Публичное событие'
    )
    
    # Статистика
    photos_count = models.PositiveIntegerField(default=0, verbose_name='Количество фото')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.date})"


class Photo(models.Model):
    """
    Модель фотографии
    """
    class Status(models.TextChoices):
        PROCESSING = 'processing', 'Обрабатывается'
        ACTIVE = 'active', 'Активно'
        SOLD = 'sold', 'Продано'
        DELETED = 'deleted', 'Удалено'
        HIDDEN = 'hidden', 'Скрыто'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Фотограф'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name='Событие'
    )
    
    # Файлы изображений
    original = models.ImageField(
        upload_to=photo_upload_path,
        verbose_name='Оригинал'
    )
    watermarked = models.ImageField(
        upload_to=watermarked_upload_path,
        blank=True,
        null=True,
        verbose_name='С водяным знаком'
    )
    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_path,
        blank=True,
        null=True,
        verbose_name='Превью'
    )
    
    # Метаданные
    title = models.CharField(max_length=300, blank=True, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    # Технические данные
    width = models.PositiveIntegerField(default=0, verbose_name='Ширина')
    height = models.PositiveIntegerField(default=0, verbose_name='Высота')
    file_size = models.PositiveIntegerField(default=0, verbose_name='Размер файла')
    
    # EXIF данные
    taken_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата съёмки')
    camera_model = models.CharField(max_length=100, blank=True, verbose_name='Камера')
    
    # Ценообразование
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Цена'
    )
    
    # Статус
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
        verbose_name='Статус'
    )
    
    # Распознавание лиц
    faces_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество лиц'
    )
    faces_processed = models.BooleanField(
        default=False,
        verbose_name='Лица обработаны'
    )
    
    # Статистика
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Фото {self.id} от {self.photographer.user.username}"


class PhotoFace(models.Model):
    """
    Лицо, найденное на фотографии
    Хранит координаты и кодировку для распознавания
    """
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='faces',
        verbose_name='Фотография'
    )
    
    # Координаты лица на фото (top, right, bottom, left)
    face_location = models.JSONField(
        verbose_name='Координаты лица'
    )
    
    # Кодировка лица (128-мерный вектор)
    face_encoding = models.JSONField(
        verbose_name='Кодировка лица'
    )
    
    # Связь с пользователем (если лицо идентифицировано)
    matched_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_faces',
        verbose_name='Распознанный пользователь'
    )
    match_confidence = models.FloatField(
        default=0.0,
        verbose_name='Уверенность совпадения'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лицо на фото'
        verbose_name_plural = 'Лица на фото'
    
    def __str__(self):
        return f"Лицо на фото {self.photo.id}"


class DeletionRequest(models.Model):
    """
    Запрос на удаление фотографии (согласно 152-ФЗ)
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'На рассмотрении'
        APPROVED = 'approved', 'Одобрено'
        REJECTED = 'rejected', 'Отклонено'
    
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='deletion_requests',
        verbose_name='Фотография'
    )
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='deletion_requests',
        verbose_name='Заявитель'
    )
    
    reason = models.TextField(verbose_name='Причина запроса')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    
    # Ответ фотографа
    response = models.TextField(blank=True, verbose_name='Ответ фотографа')
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_deletion_requests',
        verbose_name='Обработал'
    )
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата обработки')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Запрос на удаление'
        verbose_name_plural = 'Запросы на удаление'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Запрос на удаление фото {self.photo.id}"
