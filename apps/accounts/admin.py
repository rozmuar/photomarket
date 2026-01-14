from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PhotographerProfile, ClientProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительно', {
            'fields': ('user_type', 'phone', 'avatar', 
                      'consent_personal_data', 'consent_biometric_data', 'consent_date')
        }),
    )


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'studio_name', 'is_verified', 'balance', 'total_earned']
    list_filter = ['is_verified']
    search_fields = ['user__username', 'studio_name']


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'face_processed', 'total_purchases', 'total_spent']
    list_filter = ['face_processed']
    search_fields = ['user__username']
