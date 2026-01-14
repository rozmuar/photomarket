"""
Модели пользователей - Фотографы и Клиенты
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class User(AbstractUser):
    """
    Расширенная модель пользователя
    Может быть фотографом, клиентом или обоими
    """
    class UserType(models.TextChoices):
        PHOTOGRAPHER = 'photographer', 'Фотограф'
        CLIENT = 'client', 'Клиент'
        BOTH = 'both', 'Фотограф и Клиент'
    
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.CLIENT,
        verbose_name='Тип пользователя'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    
    # Согласие на обработку персональных данных (152-ФЗ)
    consent_personal_data = models.BooleanField(
        default=False,
        verbose_name='Согласие на обработку ПД'
    )
    consent_biometric_data = models.BooleanField(
        default=False,
        verbose_name='Согласие на обработку биометрии'
    )
    consent_date = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Дата согласия'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_user_type_display()})"
    
    @property
    def is_photographer(self):
        return self.user_type in [self.UserType.PHOTOGRAPHER, self.UserType.BOTH]
    
    @property
    def is_client(self):
        return self.user_type in [self.UserType.CLIENT, self.UserType.BOTH]


class PhotographerProfile(models.Model):
    """
    Профиль фотографа - дополнительные данные
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='photographer_profile',
        verbose_name='Пользователь'
    )
    
    # Информация о фотографе
    studio_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Название студии/бренда'
    )
    description = models.TextField(
        blank=True,
        verbose_name='О себе'
    )
    website = models.URLField(blank=True, verbose_name='Сайт')
    instagram = models.CharField(max_length=100, blank=True, verbose_name='Instagram')
    vk = models.CharField(max_length=100, blank=True, verbose_name='VK')
    telegram = models.CharField(max_length=100, blank=True, verbose_name='Telegram')
    
    # Верификация
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Верифицирован'
    )
    verification_document = models.FileField(
        upload_to='verification/',
        blank=True,
        null=True,
        verbose_name='Документ верификации'
    )
    
    # Финансы
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Баланс'
    )
    total_earned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Всего заработано'
    )
    
    # Реквизиты для вывода
    bank_card = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Номер карты'
    )
    
    # Настройки
    default_photo_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        verbose_name='Цена фото по умолчанию'
    )
    auto_watermark = models.BooleanField(
        default=True,
        verbose_name='Автоматический водяной знак'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Профиль фотографа'
        verbose_name_plural = 'Профили фотографов'
    
    def __str__(self):
        return f"Профиль фотографа: {self.user.username}"


class ClientProfile(models.Model):
    """
    Профиль клиента - данные для поиска по лицу
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile',
        verbose_name='Пользователь'
    )
    
    # Селфи для распознавания
    selfie = models.ImageField(
        upload_to='selfies/',
        blank=True,
        null=True,
        verbose_name='Селфи для поиска'
    )
    
    # Кодировка лица (face encoding) - хранится как JSON
    face_encoding = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Кодировка лица'
    )
    
    # Статус обработки селфи
    face_processed = models.BooleanField(
        default=False,
        verbose_name='Лицо обработано'
    )
    face_processing_error = models.TextField(
        blank=True,
        verbose_name='Ошибка обработки'
    )
    
    # Статистика
    total_purchases = models.PositiveIntegerField(
        default=0,
        verbose_name='Всего покупок'
    )
    total_spent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Всего потрачено'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Профиль клиента'
        verbose_name_plural = 'Профили клиентов'
    
    def __str__(self):
        return f"Профиль клиента: {self.user.username}"
