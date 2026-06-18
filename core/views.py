from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F
from datetime import date, timedelta
from .models import PantryItem, Recipe, RecipeIngredient, ShoppingListItem, MealPlan
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, 
    PantryItemForm, ShoppingListItemForm, MealPlanForm
)


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

@login_required(login_url='/login/')
def shopping_list(request):
    """Список покупок пользователя"""
    items = ShoppingListItem.objects.filter(user=request.user).select_related('ingredient')
    
    # Разделяем на купленные и нет
    not_purchased = items.filter(is_purchased=False).order_by('ingredient__category')
    purchased = items.filter(is_purchased=True).order_by('-added_date')
    
    # Группируем по категориям
    categories = {}
    for item in not_purchased:
        cat = item.ingredient.get_category_display()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    # Считаем общую стоимость
    total_cost = sum(
        float(item.quantity) * float(item.ingredient.price_per_unit) 
        for item in not_purchased
    )
    
    context = {
        'categories': categories,
        'purchased': purchased,
        'total_cost': total_cost,
        'total_items': not_purchased.count(),
    }
    return render(request, 'core/shopping_list.html', context)

@login_required(login_url='/login/')
def shopping_add(request):
    """Ручное добавление в список покупок"""
    if request.method == 'POST':
        form = ShoppingListItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, f'"{item.ingredient.name}" добавлен в список покупок!')
            return redirect('core:shopping_list')
    else:
        form = ShoppingListItemForm()
    return render(request, 'core/shopping_form.html', {'form': form})

@login_required(login_url='/login/')
def shopping_toggle(request, pk):
    """Переключить статус куплено/не куплено"""
    item = get_object_or_404(ShoppingListItem, pk=pk, user=request.user)
    item.is_purchased = not item.is_purchased
    item.save()
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def shopping_delete(request, pk):
    """Удалить из списка покупок"""
    item = get_object_or_404(ShoppingListItem, pk=pk, user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Удалено из списка покупок.')
        return redirect('core:shopping_list')
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def shopping_generate(request):
    """Генерация списка покупок из холодильника (истекающие/просроченные)"""
    if request.method == 'POST':
        # Находим продукты, которые истекают через 2 дня или уже просрочены
        expiring_items = PantryItem.objects.filter(
            user=request.user,
            expiry_date__lte=date.today() + timedelta(days=2)
        ).select_related('ingredient')
        
        added_count = 0
        for pantry_item in expiring_items:
            # Проверяем, нет ли уже этого продукта в списке покупок (не купленного)
            exists = ShoppingListItem.objects.filter(
                user=request.user,
                ingredient=pantry_item.ingredient,
                is_purchased=False
            ).exists()
            
            if not exists:
                ShoppingListItem.objects.create(
                    user=request.user,
                    ingredient=pantry_item.ingredient,
                    quantity=pantry_item.quantity
                )
                added_count += 1
        
        if added_count > 0:
            messages.success(request, f'Добавлено {added_count} продуктов в список покупок!')
        else:
            messages.info(request, 'Все истекающие продукты уже в списке покупок.')
        
        return redirect('core:shopping_list')
    
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def shopping_clear_purchased(request):
    """Удалить все купленные продукты"""
    if request.method == 'POST':
        count = ShoppingListItem.objects.filter(user=request.user, is_purchased=True).count()
        ShoppingListItem.objects.filter(user=request.user, is_purchased=True).delete()
        messages.success(request, f'Удалено {count} купленных продуктов.')
        return redirect('core:shopping_list')
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def meal_plan(request):
    """План питания на неделю"""
    # Получаем текущую неделю (понедельник - воскресенье)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник
    end_of_week = start_of_week + timedelta(days=6)  # Воскресенье
    
    # Получаем все планы пользователя на эту неделю
    meal_plans = MealPlan.objects.filter(
        user=request.user,
        date__range=[start_of_week, end_of_week]
    ).select_related('recipe').order_by('date', 'meal_type')
    
    # Группируем по дням
    days = []
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        day_plans = meal_plans.filter(date=current_date)
        
        # Создаём структуру для каждого приёма пищи
        day_data = {
            'date': current_date,
            'day_name': current_date.strftime('%A'),
            'breakfast': day_plans.filter(meal_type='breakfast').first(),
            'lunch': day_plans.filter(meal_type='lunch').first(),
            'dinner': day_plans.filter(meal_type='dinner').first(),
            'snack': day_plans.filter(meal_type='snack').first(),
        }
        days.append(day_data)
    
    # Считаем общую стоимость ингредиентов на неделю
    total_cost = 0
    for plan in meal_plans:
        for ingredient in plan.recipe.ingredients.all():
            quantity_needed = float(ingredient.quantity) * plan.servings_planned
            # Проверяем, есть ли в холодильнике
            pantry = PantryItem.objects.filter(
                user=request.user,
                ingredient=ingredient.ingredient,
                expiry_date__gte=current_date
            ).first()
            
            if pantry:
                quantity_to_buy = max(0, quantity_needed - float(pantry.quantity))
            else:
                quantity_to_buy = quantity_needed
            
            total_cost += quantity_to_buy * float(ingredient.ingredient.price_per_unit)
    
    context = {
        'days': days,
        'start_date': start_of_week,
        'end_date': end_of_week,
        'total_cost': total_cost,
    }
    return render(request, 'core/meal_plan.html', context)

@login_required(login_url='/login/')
def meal_plan_add(request):
    """Добавить блюдо в план питания"""
    if request.method == 'POST':
        form = MealPlanForm(request.POST)
        if form.is_valid():
            meal_plan = form.save(commit=False)
            meal_plan.user = request.user
            meal_plan.save()
            messages.success(request, f'{meal_plan.recipe.name} добавлено в план на {meal_plan.date}!')
            return redirect('core:meal_plan')
    else:
        form = MealPlanForm()
    
    return render(request, 'core/meal_plan_form.html', {'form': form, 'title': 'Добавить в план'})

@login_required(login_url='/login/')
def meal_plan_delete(request, pk):
    """Удалить из плана питания"""
    meal_plan_item = get_object_or_404(MealPlan, pk=pk, user=request.user)
    
    if request.method == 'POST':
        meal_plan_item.delete()
        messages.success(request, 'Удалено из плана питания.')
        return redirect('core:meal_plan')
    
    return render(request, 'core/meal_plan_confirm_delete.html', {'item': meal_plan_item})

@login_required(login_url='/login/')
def meal_plan_generate_shopping(request):
    """Сгенерировать список покупок из плана питания"""
    if request.method == 'POST':
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Получаем все планы на неделю
        meal_plans = MealPlan.objects.filter(
            user=request.user,
            date__range=[start_of_week, end_of_week]
        ).select_related('recipe')
        
        # Собираем все необходимые ингредиенты
        needed_ingredients = {}
        
        for plan in meal_plans:
            for recipe_ing in plan.recipe.ingredients.all():
                ing = recipe_ing.ingredient
                quantity_needed = float(recipe_ing.quantity) * plan.servings_planned
                
                if ing.id not in needed_ingredients:
                    needed_ingredients[ing.id] = {
                        'ingredient': ing,
                        'quantity': 0
                    }
                needed_ingredients[ing.id]['quantity'] += quantity_needed
        
        # Вычитаем то, что есть в холодильнике
        pantry_items = PantryItem.objects.filter(
            user=request.user,
            expiry_date__gte=today
        )
        
        for pantry_item in pantry_items:
            if pantry_item.ingredient.id in needed_ingredients:
                needed_ingredients[pantry_item.ingredient.id]['quantity'] -= float(pantry_item.quantity)
        
        # Создаём элементы списка покупок
        added_count = 0
        for ing_id, data in needed_ingredients.items():
            if data['quantity'] > 0:
                # Проверяем, нет ли уже в списке
                exists = ShoppingListItem.objects.filter(
                    user=request.user,
                    ingredient=data['ingredient'],
                    is_purchased=False
                ).first()
                
                if exists:
                    # Обновляем количество
                    exists.quantity += Decimal(str(data['quantity']))
                    exists.save()
                else:
                    # Создаём новый
                    ShoppingListItem.objects.create(
                        user=request.user,
                        ingredient=data['ingredient'],
                        quantity=Decimal(str(data['quantity']))
                    )
                added_count += 1
        
        messages.success(request, f'Список покупок сгенерирован! Добавлено {added_count} продуктов.')
        return redirect('core:shopping_list')
    
    return redirect('core:meal_plan')