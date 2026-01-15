"""
Views для кабинета фотографа
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone

from apps.accounts.models import PhotographerProfile
from apps.photos.models import Event, Photo, DeletionRequest
from apps.payments.models import Purchase, Withdrawal
from .forms import EventForm, PhotoUploadForm, BulkPhotoUploadForm, WithdrawalForm


class PhotographerRequiredMixin(UserPassesTestMixin):
    """Миксин - только для фотографов"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_photographer


class DashboardView(LoginRequiredMixin, PhotographerRequiredMixin, TemplateView):
    """Главная страница кабинета фотографа"""
    template_name = 'photographers/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.photographer_profile
        
        # Статистика
        context['profile'] = profile
        context['events_count'] = Event.objects.filter(photographer=profile).count()
        context['photos_count'] = Photo.objects.filter(photographer=profile, status='active').count()
        context['pending_requests'] = DeletionRequest.objects.filter(
            photo__photographer=profile,
            status='pending'
        ).count()
        
        # Последние продажи
        context['recent_sales'] = Purchase.objects.filter(
            photographer=profile,
            status='paid'
        ).select_related('buyer__user', 'photo')[:5]
        
        # Доход за месяц
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        month_sales = Purchase.objects.filter(
            photographer=profile,
            status='paid',
            paid_at__gte=month_start
        ).aggregate(total=Sum('photographer_amount'))
        context['month_earnings'] = month_sales['total'] or 0
        
        return context


class EventListView(LoginRequiredMixin, PhotographerRequiredMixin, ListView):
    """Список событий фотографа"""
    template_name = 'photographers/events/list.html'
    context_object_name = 'events'
    paginate_by = 10
    
    def get_queryset(self):
        return Event.objects.filter(
            photographer=self.request.user.photographer_profile
        ).order_by('-date')


class EventCreateView(LoginRequiredMixin, PhotographerRequiredMixin, CreateView):
    """Создание события"""
    template_name = 'photographers/events/form.html'
    form_class = EventForm
    success_url = reverse_lazy('photographers:events')
    
    def form_valid(self, form):
        form.instance.photographer = self.request.user.photographer_profile
        messages.success(self.request, 'Событие создано!')
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, PhotographerRequiredMixin, UpdateView):
    """Редактирование события"""
    template_name = 'photographers/events/form.html'
    form_class = EventForm
    success_url = reverse_lazy('photographers:events')
    
    def get_queryset(self):
        return Event.objects.filter(photographer=self.request.user.photographer_profile)
    
    def form_valid(self, form):
        messages.success(self.request, 'Событие обновлено!')
        return super().form_valid(form)


class EventDetailView(LoginRequiredMixin, PhotographerRequiredMixin, DetailView):
    """Детали события с фотографиями"""
    template_name = 'photographers/events/detail.html'
    context_object_name = 'event'
    
    def get_queryset(self):
        return Event.objects.filter(photographer=self.request.user.photographer_profile)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photos'] = Photo.objects.filter(event=self.object).order_by('-created_at')
        return context


class PhotoListView(LoginRequiredMixin, PhotographerRequiredMixin, ListView):
    """Все фотографии фотографа"""
    template_name = 'photographers/photos/list.html'
    context_object_name = 'photos'
    paginate_by = 20
    
    def get_queryset(self):
        return Photo.objects.filter(
            photographer=self.request.user.photographer_profile
        ).select_related('event').order_by('-created_at')


@login_required
def photo_upload(request):
    """Загрузка фотографий"""
    if not request.user.is_photographer:
        return redirect('accounts:dashboard')
    
    profile = request.user.photographer_profile
    
    if request.method == 'POST':
        form = BulkPhotoUploadForm(profile, request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('photos')
            event = form.cleaned_data.get('event')
            price = form.cleaned_data['price']
            
            # Импортируем сервис обработки
            from apps.photos.services import photo_service
            
            processed = 0
            for f in files:
                photo = Photo.objects.create(
                    photographer=profile,
                    event=event,
                    original=f,
                    price=price,
                    status='processing'
                )
                # Обрабатываем фото (превью, водяной знак, лица)
                if photo_service.process_photo(photo):
                    processed += 1
            
            # Обновляем счётчик фото у события
            if event:
                event.photos_count = Photo.objects.filter(event=event, status='active').count()
                event.save()
            
            messages.success(request, f'Загружено и обработано {processed} из {len(files)} фото!')
            return redirect('photographers:photos')
    else:
        form = BulkPhotoUploadForm(profile)
    
    return render(request, 'photographers/photos/upload.html', {'form': form})


class SalesListView(LoginRequiredMixin, PhotographerRequiredMixin, ListView):
    """История продаж"""
    template_name = 'photographers/sales.html'
    context_object_name = 'sales'
    paginate_by = 20
    
    def get_queryset(self):
        return Purchase.objects.filter(
            photographer=self.request.user.photographer_profile,
            status='paid'
        ).select_related('buyer__user', 'photo').order_by('-paid_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.photographer_profile
        
        total = Purchase.objects.filter(
            photographer=profile, status='paid'
        ).aggregate(total=Sum('photographer_amount'))
        context['total_earned'] = total['total'] or 0
        
        return context


class DeletionRequestListView(LoginRequiredMixin, PhotographerRequiredMixin, ListView):
    """Запросы на удаление"""
    template_name = 'photographers/deletion_requests.html'
    context_object_name = 'requests'
    paginate_by = 10
    
    def get_queryset(self):
        return DeletionRequest.objects.filter(
            photo__photographer=self.request.user.photographer_profile
        ).select_related('photo', 'requester').order_by('-created_at')


@login_required
def process_deletion_request(request, pk):
    """Обработка запроса на удаление"""
    if not request.user.is_photographer:
        return redirect('accounts:dashboard')
    
    deletion_request = get_object_or_404(
        DeletionRequest,
        pk=pk,
        photo__photographer=request.user.photographer_profile
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        response = request.POST.get('response', '')
        
        if action == 'approve':
            deletion_request.status = 'approved'
            deletion_request.photo.status = 'deleted'
            deletion_request.photo.save()
            messages.success(request, 'Запрос одобрен, фото удалено.')
        elif action == 'reject':
            deletion_request.status = 'rejected'
            messages.info(request, 'Запрос отклонён.')
        
        deletion_request.response = response
        deletion_request.processed_by = request.user
        deletion_request.processed_at = timezone.now()
        deletion_request.save()
        
        return redirect('photographers:deletion_requests')
    
    return render(request, 'photographers/deletion_request_detail.html', {
        'request': deletion_request
    })


@login_required
def withdrawal_request(request):
    """Запрос на вывод средств"""
    if not request.user.is_photographer:
        return redirect('accounts:dashboard')
    
    profile = request.user.photographer_profile
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            if amount > profile.balance:
                messages.error(request, 'Недостаточно средств на балансе.')
            else:
                Withdrawal.objects.create(
                    photographer=profile,
                    amount=amount,
                    bank_card=form.cleaned_data['bank_card']
                )
                profile.balance -= amount
                profile.save()
                messages.success(request, f'Заявка на вывод {amount}₽ создана.')
                return redirect('photographers:dashboard')
    else:
        form = WithdrawalForm(initial={'bank_card': profile.bank_card})
    
    return render(request, 'photographers/withdrawal.html', {
        'form': form,
        'balance': profile.balance
    })
