from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import PantryItem, Ingredient
from datetime import date, timedelta

class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации"""
    email = forms.EmailField(required=True, label='Email')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Имя пользователя',
        }

class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа"""
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class PantryItemForm(forms.ModelForm):
    """Форма добавления продукта в холодильник"""
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        label='Продукт',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        min_value=0.01,
        label='Количество',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    expiry_date = forms.DateField(
        label='Срок годности',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = PantryItem
        fields = ['ingredient', 'quantity', 'expiry_date']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Установим минимальную дату - сегодня
        self.fields['expiry_date'].widget.attrs['min'] = date.today().isoformat()