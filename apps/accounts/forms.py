"""
Формы аутентификации и профиля
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import User, PhotographerProfile, ClientProfile


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    
    USER_TYPE_CHOICES = [
        ('client', 'Я хочу найти свои фотографии'),
        ('photographer', 'Я фотограф и хочу продавать фото'),
    ]
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Выберите тип аккаунта'
    )
    consent_personal_data = forms.BooleanField(
        required=True,
        label='Я согласен на обработку персональных данных',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    consent_biometric_data = forms.BooleanField(
        required=True,
        label='Я согласен на обработку биометрических данных (распознавание лица)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтвердите пароль'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = self.cleaned_data['user_type']
        user.consent_personal_data = self.cleaned_data['consent_personal_data']
        user.consent_biometric_data = self.cleaned_data['consent_biometric_data']
        user.consent_date = timezone.now()
        
        if commit:
            user.save()
            # Создаём соответствующий профиль
            if user.user_type == 'photographer':
                PhotographerProfile.objects.create(user=user)
            elif user.user_type == 'client':
                ClientProfile.objects.create(user=user)
        
        return user


class CustomLoginForm(AuthenticationForm):
    """Кастомная форма входа"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин или Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PhotographerProfileForm(forms.ModelForm):
    """Форма профиля фотографа"""
    
    class Meta:
        model = PhotographerProfile
        fields = [
            'studio_name', 'description', 'website',
            'instagram', 'vk', 'telegram',
            'default_photo_price', 'auto_watermark', 'bank_card'
        ]
        widgets = {
            'studio_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'vk': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'vk.com/username'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'default_photo_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'auto_watermark': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'bank_card': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000 0000 0000 0000'}),
        }


class ClientProfileForm(forms.ModelForm):
    """Форма профиля клиента"""
    
    class Meta:
        model = ClientProfile
        fields = ['selfie']
        widgets = {
            'selfie': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'capture': 'user'  # Открывает фронтальную камеру на мобильных
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selfie'].label = 'Загрузите селфи для поиска ваших фотографий'
        self.fields['selfie'].help_text = 'Лицо должно быть хорошо видно. Фото используется только для поиска.'
