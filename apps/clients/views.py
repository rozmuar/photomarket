"""
Views для кабинета клиента
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q

from apps.accounts.models import ClientProfile
from apps.photos.models import Photo, PhotoFace, DeletionRequest
from apps.payments.models import Purchase
from .forms import SelfieUploadForm, DeletionRequestForm, SearchFilterForm


class ClientRequiredMixin(UserPassesTestMixin):
    """Миксин - только для клиентов"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_client


class DashboardView(LoginRequiredMixin, ClientRequiredMixin, TemplateView):
    """Главная страница кабинета клиента"""
    template_name = 'clients/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = ClientProfile.objects.get_or_create(user=self.request.user)
        
        context['profile'] = profile
        context['selfie_form'] = SelfieUploadForm(instance=profile)
        
        # Найденные фото (где есть совпадение с лицом пользователя)
        if profile.face_processed:
            # Исключаем фото с активными запросами на удаление
            pending_deletion_photo_ids = DeletionRequest.objects.filter(
                status='pending'
            ).values_list('photo_id', flat=True)
            
            matched_faces = PhotoFace.objects.filter(
                matched_user=self.request.user,
                photo__status='active'
            ).exclude(
                photo_id__in=pending_deletion_photo_ids
            ).select_related('photo')
            
            context['matched_photos_count'] = matched_faces.count()
            context['recent_matches'] = [f.photo for f in matched_faces[:6]]
        
        # Мои покупки
        context['purchases'] = Purchase.objects.filter(
            buyer=profile,
            status='paid'
        ).select_related('photo')[:5]
        
        # Мои запросы на удаление
        context['deletion_requests'] = DeletionRequest.objects.filter(
            requester=self.request.user
        ).select_related('photo')[:5]
        
        return context


@login_required
def upload_selfie(request):
    """Загрузка/обновление селфи"""
    if not request.user.is_client:
        return redirect('accounts:dashboard')
    
    profile, _ = ClientProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = SelfieUploadForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.face_processed = False
            profile.face_encoding = None
            profile.save()
            
            # Обрабатываем селфи и ищем совпадения
            from apps.recognition.services import face_service
            
            if face_service.available:
                try:
                    # Получаем кодировку лица с селфи
                    faces = face_service.get_face_data(profile.selfie.path)
                    
                    if faces:
                        # Сохраняем кодировку первого (основного) лица
                        profile.face_encoding = faces[0]['encoding']
                        profile.face_processed = True
                        profile.save()
                        
                        # Ищем совпадения на всех фото
                        from apps.photos.models import PhotoFace
                        
                        matched_count = 0
                        for photo_face in PhotoFace.objects.filter(matched_user__isnull=True):
                            if photo_face.face_encoding:
                                is_match, confidence = face_service.compare_faces(
                                    profile.face_encoding,
                                    photo_face.face_encoding
                                )
                                if is_match:
                                    photo_face.matched_user = request.user
                                    photo_face.save()
                                    matched_count += 1
                        
                        messages.success(request, f'Селфи обработано! Найдено {matched_count} фото с вами.')
                    else:
                        messages.warning(request, 'Лицо не найдено на селфи. Попробуйте другое фото.')
                except Exception as e:
                    messages.error(request, f'Ошибка обработки: {e}')
                    profile.face_processed = True  # Помечаем как обработанное, чтобы не зависло
                    profile.save()
            else:
                profile.face_processed = True
                profile.save()
                messages.info(request, 'Селфи загружено. Распознавание лиц временно недоступно.')
            
            return redirect('clients:dashboard')
    else:
        form = SelfieUploadForm(instance=profile)
    
    return render(request, 'clients/upload_selfie.html', {'form': form})


class MyPhotosView(LoginRequiredMixin, ClientRequiredMixin, ListView):
    """Фотографии, найденные по лицу клиента"""
    template_name = 'clients/my_photos.html'
    context_object_name = 'photos'
    paginate_by = 20
    
    def get_queryset(self):
        profile = self.request.user.client_profile
        
        if not profile.face_processed:
            return Photo.objects.none()
        
        # Получаем фото, на которых найдено лицо пользователя
        matched_photo_ids = PhotoFace.objects.filter(
            matched_user=self.request.user
        ).values_list('photo_id', flat=True)
        
        # Исключаем фото с активными запросами на удаление
        pending_deletion_photo_ids = DeletionRequest.objects.filter(
            status='pending'
        ).values_list('photo_id', flat=True)
        
        queryset = Photo.objects.filter(
            id__in=matched_photo_ids,
            status='active'
        ).exclude(
            id__in=pending_deletion_photo_ids
        ).select_related('photographer__user', 'event')
        
        # Применяем фильтры
        form = SearchFilterForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('event_type'):
                queryset = queryset.filter(event__event_type=form.cleaned_data['event_type'])
            if form.cleaned_data.get('city'):
                queryset = queryset.filter(event__city__icontains=form.cleaned_data['city'])
            if form.cleaned_data.get('date_from'):
                queryset = queryset.filter(event__date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                queryset = queryset.filter(event__date__lte=form.cleaned_data['date_to'])
            if form.cleaned_data.get('price_min'):
                queryset = queryset.filter(price__gte=form.cleaned_data['price_min'])
            if form.cleaned_data.get('price_max'):
                queryset = queryset.filter(price__lte=form.cleaned_data['price_max'])
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = SearchFilterForm(self.request.GET)
        context['profile'] = self.request.user.client_profile
        return context


class PhotoDetailView(LoginRequiredMixin, DetailView):
    """Детальный просмотр фотографии - доступно всем авторизованным"""
    template_name = 'clients/photo_detail.html'
    context_object_name = 'photo'
    
    def get_queryset(self):
        return Photo.objects.filter(status='active').select_related('photographer__user', 'event')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Проверяем, куплено ли уже это фото (только для клиентов)
        context['is_purchased'] = False
        context['is_client'] = self.request.user.is_client
        
        if self.request.user.is_client:
            profile, _ = ClientProfile.objects.get_or_create(user=self.request.user)
            context['is_purchased'] = Purchase.objects.filter(
                buyer=profile,
                photo=self.object,
                status='paid'
            ).exists()
            
            # Форма запроса на удаление
            context['deletion_form'] = DeletionRequestForm()
            
            # Есть ли активный (pending) запрос на удаление
            context['deletion_request'] = DeletionRequest.objects.filter(
                photo=self.object,
                requester=self.request.user,
                status='pending'
            ).first()
            
            # Последний отклонённый запрос (для показа причины отказа)
            if not context['deletion_request']:
                context['rejected_request'] = DeletionRequest.objects.filter(
                    photo=self.object,
                    requester=self.request.user,
                    status='rejected'
                ).order_by('-processed_at').first()
        
        return context


@login_required
def request_deletion(request, photo_id):
    """Запрос на удаление фотографии"""
    if not request.user.is_client:
        return redirect('accounts:dashboard')
    
    photo = get_object_or_404(Photo, id=photo_id, status='active')
    
    # Проверяем, есть ли уже активный запрос (pending)
    existing = DeletionRequest.objects.filter(
        photo=photo, 
        requester=request.user,
        status='pending'
    ).first()
    
    if existing:
        messages.warning(request, 'Вы уже отправляли запрос на удаление этого фото. Ожидайте ответа.')
        return redirect('clients:photo_detail', pk=photo_id)
    
    if request.method == 'POST':
        form = DeletionRequestForm(request.POST)
        if form.is_valid():
            deletion_request = form.save(commit=False)
            deletion_request.photo = photo
            deletion_request.requester = request.user
            deletion_request.save()
            
            messages.success(request, 'Запрос на удаление отправлен фотографу.')
            return redirect('clients:photo_detail', pk=photo_id)
    
    return redirect('clients:photo_detail', pk=photo_id)


class PurchasesView(LoginRequiredMixin, ClientRequiredMixin, ListView):
    """Список покупок клиента"""
    template_name = 'clients/purchases.html'
    context_object_name = 'purchases'
    paginate_by = 20
    
    def get_queryset(self):
        return Purchase.objects.filter(
            buyer=self.request.user.client_profile
        ).select_related('photo', 'photographer__user').order_by('-created_at')


class DeletionRequestsView(LoginRequiredMixin, ClientRequiredMixin, ListView):
    """Мои запросы на удаление"""
    template_name = 'clients/deletion_requests.html'
    context_object_name = 'requests'
    paginate_by = 10
    
    def get_queryset(self):
        return DeletionRequest.objects.filter(
            requester=self.request.user
        ).select_related('photo', 'photo__photographer__user').order_by('-created_at')


@login_required
def search_photos(request):
    """Повторный поиск фото по базе (для клиентов с загруженным селфи)"""
    if not request.user.is_client:
        messages.error(request, 'Только для клиентов.')
        return redirect('accounts:dashboard')
    
    try:
        profile = request.user.client_profile
    except ClientProfile.DoesNotExist:
        messages.error(request, 'Профиль не найден.')
        return redirect('clients:dashboard')
    
    if not profile.selfie:
        messages.warning(request, 'Сначала загрузите своё селфи.')
        return redirect('clients:dashboard')
    
    from apps.recognition.services import face_service
    
    if not face_service.available:
        messages.error(request, 'Сервис распознавания лиц временно недоступен.')
        return redirect('clients:dashboard')
    
    # Если нет кодировки лица - пробуем получить
    if not profile.face_encoding:
        try:
            faces = face_service.get_face_data(profile.selfie.path)
            if faces:
                profile.face_encoding = faces[0]['encoding']
                profile.face_processed = True
                profile.save()
            else:
                messages.warning(request, 'Лицо не найдено на селфи. Попробуйте другое фото.')
                return redirect('clients:dashboard')
        except Exception as e:
            messages.error(request, f'Ошибка обработки селфи: {e}')
            return redirect('clients:dashboard')
    
    # Ищем совпадения во всех фото, где ещё нет совпадений с этим пользователем
    from apps.photos.models import PhotoFace
    
    matched_count = 0
    new_matches = 0
    
    # Получаем все лица на фото
    all_faces = PhotoFace.objects.select_related('photo').all()
    
    for photo_face in all_faces:
        if photo_face.face_encoding:
            try:
                is_match, confidence = face_service.compare_faces(
                    profile.face_encoding,
                    photo_face.face_encoding
                )
                if is_match:
                    matched_count += 1
                    if photo_face.matched_user != request.user:
                        photo_face.matched_user = request.user
                        photo_face.save()
                        new_matches += 1
            except Exception:
                continue
    
    if new_matches > 0:
        messages.success(request, f'Поиск завершён! Найдено {new_matches} новых фото с вами. Всего совпадений: {matched_count}.')
    elif matched_count > 0:
        messages.info(request, f'Найдено {matched_count} фото с вами. Новых совпадений нет.')
    else:
        messages.info(request, 'К сожалению, фото с вами пока не найдено.')
    
    return redirect('clients:dashboard')
