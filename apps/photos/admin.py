from django.contrib import admin
from .models import Event, Photo, PhotoFace, DeletionRequest


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'photographer', 'event_type', 'date', 'city', 'photos_count', 'is_public']
    list_filter = ['event_type', 'is_public', 'date']
    search_fields = ['name', 'location', 'city']
    date_hierarchy = 'date'


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'photographer', 'event', 'status', 'price', 'faces_count', 'views_count', 'created_at']
    list_filter = ['status', 'faces_processed', 'created_at']
    search_fields = ['id', 'photographer__user__username', 'title']
    readonly_fields = ['faces_count', 'faces_processed', 'width', 'height', 'file_size']


@admin.register(PhotoFace)
class PhotoFaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'photo', 'matched_user', 'match_confidence', 'created_at']
    list_filter = ['created_at']
    search_fields = ['photo__id', 'matched_user__username']


@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'photo', 'requester', 'status', 'created_at', 'processed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['photo__id', 'requester__username', 'reason']
