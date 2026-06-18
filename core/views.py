from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import Recipe
from .models import PantryItem, Recipe, RecipeIngredient
from .forms import CustomUserCreationForm, CustomAuthenticationForm, PantryItemForm
from django.db.models import Sum, F
from datetime import date, timedelta

def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, 'core/recipe_list.html', {'recipes': recipes})

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'core/recipe_detail.html', {'recipe': recipe})

def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Регистрация успешна! Добро пожаловать, {user.username}!')
            return redirect('core:recipe_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    """Вход пользователя"""
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'С возвращением, {user.username}!')
            return redirect('core:recipe_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required(login_url='/login/')
def user_logout(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('core:recipe_list')

@login_required(login_url='/login/')
def pantry_list(request):
    """Список продуктов в холодильнике"""
    # Получаем все продукты пользователя
    pantry_items = PantryItem.objects.filter(user=request.user).select_related('ingredient')
    
    # Сортируем: сначала истекающие
    pantry_items = pantry_items.order_by('expiry_date')
    
    # Продукты, которые истекают через 2 дня или меньше
    expiring_soon = pantry_items.filter(
        expiry_date__lte=date.today() + timedelta(days=2)
    )
    
    # Просроченные продукты
    expired = pantry_items.filter(expiry_date__lt=date.today())
    
    context = {
        'pantry_items': pantry_items,
        'expiring_soon': expiring_soon,
        'expired': expired,
    }
    return render(request, 'core/pantry.html', context)

@login_required(login_url='/login/')
def pantry_add(request):
    """Добавление продукта в холодильник"""
    if request.method == 'POST':
        form = PantryItemForm(request.POST)
        if form.is_valid():
            pantry_item = form.save(commit=False)
            pantry_item.user = request.user
            pantry_item.save()
            messages.success(request, f'Продукт "{pantry_item.ingredient.name}" добавлен в холодильник!')
            return redirect('core:pantry_list')
    else:
        form = PantryItemForm()
    return render(request, 'core/pantry_form.html', {'form': form, 'title': 'Добавить продукт'})

@login_required(login_url='/login/')
def pantry_edit(request, pk):
    """Редактирование продукта"""
    pantry_item = get_object_or_404(PantryItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = PantryItemForm(request.POST, instance=pantry_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Продукт обновлён!')
            return redirect('core:pantry_list')
    else:
        form = PantryItemForm(instance=pantry_item)
    
    return render(request, 'core/pantry_form.html', {'form': form, 'title': 'Изменить продукт'})

@login_required(login_url='/login/')
def pantry_delete(request, pk):
    """Удаление продукта"""
    pantry_item = get_object_or_404(PantryItem, pk=pk, user=request.user)
    
    if request.method == 'POST':
        pantry_item.delete()
        messages.success(request, 'Продукт удалён из холодильника.')
        return redirect('core:pantry_list')
    
    return render(request, 'core/pantry_confirm_delete.html', {'item': pantry_item})