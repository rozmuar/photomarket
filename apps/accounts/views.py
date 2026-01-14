"""
Views для аутентификации и профиля
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import (
    UserRegistrationForm, CustomLoginForm,
    UserProfileForm, PhotographerProfileForm, ClientProfileForm
)
from .models import User, PhotographerProfile, ClientProfile


class RegisterView(CreateView):
    """Регистрация нового пользователя"""
    template_name = 'accounts/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('accounts:dashboard')
    
    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Добро пожаловать в PhotoMarket!')
        return redirect(self.success_url)


class CustomLoginView(LoginView):
    """Вход в систему"""
    template_name = 'accounts/login.html'
    authentication_form = CustomLoginForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Выход из системы"""
    next_page = 'home'


class DashboardView(LoginRequiredMixin, TemplateView):
    """Дашборд - перенаправляет в нужный кабинет"""
    template_name = 'accounts/dashboard.html'
    
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_photographer and not user.is_client:
            return redirect('photographers:dashboard')
        elif user.is_client and not user.is_photographer:
            return redirect('clients:dashboard')
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_photographer:
            context['photographer_profile'] = getattr(user, 'photographer_profile', None)
        if user.is_client:
            context['client_profile'] = getattr(user, 'client_profile', None)
        
        return context


@login_required
def profile_edit(request):
    """Редактирование профиля пользователя"""
    user = request.user
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        
        photographer_form = None
        client_form = None
        
        if user.is_photographer:
            profile, _ = PhotographerProfile.objects.get_or_create(user=user)
            photographer_form = PhotographerProfileForm(request.POST, instance=profile)
        
        if user.is_client:
            profile, _ = ClientProfile.objects.get_or_create(user=user)
            client_form = ClientProfileForm(request.POST, request.FILES, instance=profile)
        
        forms_valid = user_form.is_valid()
        if photographer_form:
            forms_valid = forms_valid and photographer_form.is_valid()
        if client_form:
            forms_valid = forms_valid and client_form.is_valid()
        
        if forms_valid:
            user_form.save()
            if photographer_form:
                photographer_form.save()
            if client_form:
                client_form.save()
            messages.success(request, 'Профиль успешно обновлён!')
            return redirect('accounts:profile')
    else:
        user_form = UserProfileForm(instance=user)
        photographer_form = None
        client_form = None
        
        if user.is_photographer:
            profile, _ = PhotographerProfile.objects.get_or_create(user=user)
            photographer_form = PhotographerProfileForm(instance=profile)
        
        if user.is_client:
            profile, _ = ClientProfile.objects.get_or_create(user=user)
            client_form = ClientProfileForm(instance=profile)
    
    return render(request, 'accounts/profile_edit.html', {
        'user_form': user_form,
        'photographer_form': photographer_form,
        'client_form': client_form,
    })


@login_required
def profile_view(request):
    """Просмотр профиля"""
    user = request.user
    context = {'user': user}
    
    if user.is_photographer:
        context['photographer_profile'] = getattr(user, 'photographer_profile', None)
    if user.is_client:
        context['client_profile'] = getattr(user, 'client_profile', None)
    
    return render(request, 'accounts/profile.html', context)
