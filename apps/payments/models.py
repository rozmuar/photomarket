"""
Модели платежей и транзакций
"""
import uuid
from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.accounts.models import User, PhotographerProfile, ClientProfile
from apps.photos.models import Photo


class Purchase(models.Model):
    """
    Покупка фотографии
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает оплаты'
        PAID = 'paid', 'Оплачено'
        FAILED = 'failed', 'Ошибка оплаты'
        REFUNDED = 'refunded', 'Возвращено'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    buyer = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='Покупатель'
    )
    photo = models.ForeignKey(
        Photo,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='Фотография'
    )
    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name='sales',
        verbose_name='Фотограф'
    )
    
    # Суммы
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма покупки'
    )
    commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Комиссия сервиса'
    )
    photographer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма фотографу'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    
    # Данные платежа YooKassa
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID платежа YooKassa'
    )
    payment_url = models.URLField(
        blank=True,
        verbose_name='Ссылка на оплату'
    )
    
    # Ссылка на скачивание (после оплаты)
    download_token = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Токен скачивания'
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество скачиваний'
    )
    max_downloads = models.PositiveIntegerField(
        default=5,
        verbose_name='Максимум скачиваний'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')
    
    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Покупка {self.id} - {self.buyer.user.username}"
    
    def save(self, *args, **kwargs):
        # Расчёт комиссии
        if not self.commission:
            commission_percent = Decimal(str(settings.SERVICE_COMMISSION_PERCENT)) / 100
            self.commission = self.amount * commission_percent
            self.photographer_amount = self.amount - self.commission
        super().save(*args, **kwargs)


class Withdrawal(models.Model):
    """
    Вывод средств фотографом
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'На рассмотрении'
        PROCESSING = 'processing', 'Обрабатывается'
        COMPLETED = 'completed', 'Выполнено'
        REJECTED = 'rejected', 'Отклонено'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    photographer = models.ForeignKey(
        PhotographerProfile,
        on_delete=models.CASCADE,
        related_name='withdrawals',
        verbose_name='Фотограф'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма вывода'
    )
    
    # Реквизиты
    bank_card = models.CharField(
        max_length=20,
        verbose_name='Номер карты'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус'
    )
    
    # Обработка
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_withdrawals',
        verbose_name='Обработал'
    )
    rejection_reason = models.TextField(blank=True, verbose_name='Причина отказа')
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Вывод средств'
        verbose_name_plural = 'Выводы средств'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Вывод {self.amount}₽ - {self.photographer.user.username}"


class Transaction(models.Model):
    """
    История транзакций (для отчётности)
    """
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', 'Покупка фото'
        SALE = 'sale', 'Продажа фото'
        WITHDRAWAL = 'withdrawal', 'Вывод средств'
        REFUND = 'refund', 'Возврат'
        COMMISSION = 'commission', 'Комиссия'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Пользователь'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        verbose_name='Тип транзакции'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма'
    )
    
    # Связи
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Покупка'
    )
    withdrawal = models.ForeignKey(
        Withdrawal,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='Вывод'
    )
    
    description = models.TextField(blank=True, verbose_name='Описание')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount}₽"
