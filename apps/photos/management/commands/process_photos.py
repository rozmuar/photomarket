"""
Команда для обработки всех фотографий
Создаёт превью, водяные знаки, распознаёт лица
"""
from django.core.management.base import BaseCommand
from apps.photos.models import Photo
from apps.photos.services import photo_service


class Command(BaseCommand):
    help = 'Обрабатывает все фотографии (превью, водяные знаки, распознавание лиц)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Обработать все фото, включая уже обработанные',
        )
        parser.add_argument(
            '--status',
            type=str,
            default='processing',
            help='Обрабатывать только фото с указанным статусом (по умолчанию: processing)',
        )

    def handle(self, *args, **options):
        if options['all']:
            photos = Photo.objects.all()
            self.stdout.write(f'Обработка ВСЕХ фото ({photos.count()} шт.)...')
        else:
            # Обрабатываем фото без превью или с указанным статусом
            photos = Photo.objects.filter(thumbnail='') | Photo.objects.filter(status=options['status'])
            photos = photos.distinct()
            self.stdout.write(f'Обработка необработанных фото ({photos.count()} шт.)...')
        
        success = 0
        errors = 0
        
        for photo in photos:
            self.stdout.write(f'  Обработка {photo.id}...', ending=' ')
            try:
                if photo_service.process_photo(photo):
                    self.stdout.write(self.style.SUCCESS('OK'))
                    success += 1
                else:
                    self.stdout.write(self.style.ERROR('ОШИБКА'))
                    errors += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'ОШИБКА: {e}'))
                errors += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Успешно: {success}'))
        if errors:
            self.stdout.write(self.style.ERROR(f'Ошибок: {errors}'))
