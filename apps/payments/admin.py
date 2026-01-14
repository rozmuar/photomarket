from django.contrib import admin
from .models import Purchase, Withdrawal, Transaction


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'buyer', 'photo', 'amount', 'commission', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'buyer__user__username', 'photo__id']
    readonly_fields = ['commission', 'photographer_amount']


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ['id', 'photographer', 'amount', 'bank_card', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['photographer__user__username', 'bank_card']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'transaction_type', 'amount', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'description']
