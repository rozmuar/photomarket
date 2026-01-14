"""
Формы для кабинета фотографа
"""
from django import forms
from apps.photos.models import Event, Photo


class EventForm(forms.ModelForm):
    """Форма создания/редактирования события"""
    
    class Meta:
        model = Event
        fields = ['name', 'event_type', 'description', 'location', 'city', 'date', 'default_price', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название события'}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес или место'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Москва'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'default_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '50'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PhotoUploadForm(forms.ModelForm):
    """Форма загрузки одного фото"""
    
    class Meta:
        model = Photo
        fields = ['original', 'event', 'title', 'price']
        widgets = {
            'original': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'event': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название (необязательно)'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '50'}),
        }
    
    def __init__(self, photographer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(photographer=photographer)
        self.fields['event'].required = False


class MultipleFileInput(forms.FileInput):
    """Виджет для загрузки нескольких файлов"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Поле для загрузки нескольких файлов"""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class BulkPhotoUploadForm(forms.Form):
    """Форма массовой загрузки фото"""
    
    photos = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        label='Фотографии'
    )
    event = forms.ModelChoiceField(
        queryset=Event.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Событие'
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        initial=500,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '50'}),
        label='Цена за фото'
    )
    
    def __init__(self, photographer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(photographer=photographer)


class WithdrawalForm(forms.Form):
    """Форма вывода средств"""
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 100, 'step': '100'}),
        label='Сумма вывода'
    )
    bank_card = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0000 0000 0000 0000',
            'pattern': '[0-9 ]{16,19}'
        }),
        label='Номер карты'
    )
