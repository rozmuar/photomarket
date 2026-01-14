"""
Формы для кабинета клиента
"""
from django import forms
from apps.accounts.models import ClientProfile
from apps.photos.models import DeletionRequest


class SelfieUploadForm(forms.ModelForm):
    """Форма загрузки селфи для поиска"""
    
    class Meta:
        model = ClientProfile
        fields = ['selfie']
        widgets = {
            'selfie': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'capture': 'user',
                'id': 'selfie-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['selfie'].label = ''
        self.fields['selfie'].help_text = 'Сделайте селфи или загрузите фото. Лицо должно быть хорошо видно.'


class DeletionRequestForm(forms.ModelForm):
    """Форма запроса на удаление фотографии"""
    
    class Meta:
        model = DeletionRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Укажите причину, почему вы хотите удалить это фото...'
            }),
        }
        labels = {
            'reason': 'Причина запроса на удаление'
        }


class SearchFilterForm(forms.Form):
    """Фильтр поиска фотографий"""
    
    EVENT_TYPE_CHOICES = [('', 'Все события')] + [
        ('wedding', 'Свадьба'),
        ('sport', 'Спортивное мероприятие'),
        ('concert', 'Концерт'),
        ('corporate', 'Корпоратив'),
        ('party', 'Вечеринка'),
        ('graduation', 'Выпускной'),
        ('children', 'Детский праздник'),
        ('other', 'Другое'),
    ]
    
    event_type = forms.ChoiceField(
        choices=EVENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Город'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    price_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'От',
            'min': 0
        })
    )
    price_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'До',
            'min': 0
        })
    )
