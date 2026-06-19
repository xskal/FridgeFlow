from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Count
from datetime import date, timedelta
from .models import PantryItem, Recipe, RecipeIngredient, ShoppingListItem, MealPlan
from .forms import (
    CustomUserCreationForm, CustomAuthenticationForm, 
    PantryItemForm, ShoppingListItemForm, MealPlanForm
)
from decimal import Decimal
import plotly.graph_objs as go
import plotly.offline as op


def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, 'core/recipe_list.html', {'recipes': recipes})

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'core/recipe_detail.html', {'recipe': recipe})

def register(request):
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
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('core:recipe_list')

@login_required(login_url='/login/')
def pantry_list(request):
    today = date.today()
    
    pantry_items = PantryItem.objects.filter(user=request.user).select_related('ingredient')
    
    pantry_items = pantry_items.order_by('expiry_date')
    
    expiring_soon = pantry_items.filter(
        expiry_date__lte=today + timedelta(days=2)
    )
    
    expired = pantry_items.filter(expiry_date__lt=today)
    
    context = {
        'pantry_items': pantry_items,
        'expiring_soon': expiring_soon,
        'expired': expired,
        'today': today,
    }
    return render(request, 'core/pantry.html', context)

@login_required(login_url='/login/')
def pantry_add(request):
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
    items = ShoppingListItem.objects.filter(user=request.user).select_related('ingredient')
    
    not_purchased = items.filter(is_purchased=False).order_by('ingredient__category')
    purchased = items.filter(is_purchased=True).order_by('-added_date')
    
    categories = {}
    for item in not_purchased:
        cat = item.ingredient.get_category_display()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
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
    item = get_object_or_404(ShoppingListItem, pk=pk, user=request.user)
    item.is_purchased = not item.is_purchased
    item.save()
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def shopping_delete(request, pk):
    item = get_object_or_404(ShoppingListItem, pk=pk, user=request.user)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Удалено из списка покупок.')
        return redirect('core:shopping_list')
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def shopping_generate(request):
    if request.method == 'POST':
        expiring_items = PantryItem.objects.filter(
            user=request.user,
            expiry_date__lte=date.today() + timedelta(days=2)
        ).select_related('ingredient')
        
        added_count = 0
        for pantry_item in expiring_items:
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
    if request.method == 'POST':
        count = ShoppingListItem.objects.filter(user=request.user, is_purchased=True).count()
        ShoppingListItem.objects.filter(user=request.user, is_purchased=True).delete()
        messages.success(request, f'Удалено {count} купленных продуктов.')
        return redirect('core:shopping_list')
    return redirect('core:shopping_list')

@login_required(login_url='/login/')
def meal_plan(request):
    """План питания на неделю"""
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  # Понедельник
    end_of_week = start_of_week + timedelta(days=6)  # Воскресенье
    
    meal_plans = MealPlan.objects.filter(
        user=request.user,
        date__range=[start_of_week, end_of_week]
    ).select_related('recipe').order_by('date', 'meal_type')
    
    days = []
    for i in range(7):
        current_date = start_of_week + timedelta(days=i)
        day_plans = meal_plans.filter(date=current_date)
        
        day_data = {
            'date': current_date,
            'day_name': current_date.strftime('%A'),
            'breakfast': day_plans.filter(meal_type='breakfast').first(),
            'lunch': day_plans.filter(meal_type='lunch').first(),
            'dinner': day_plans.filter(meal_type='dinner').first(),
            'snack': day_plans.filter(meal_type='snack').first(),
        }
        days.append(day_data)
    
    total_cost = 0
    for plan in meal_plans:
        for ingredient in plan.recipe.ingredients.all():
            quantity_needed = float(ingredient.quantity) * plan.servings_planned
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
    if request.method == 'POST':
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        meal_plans = MealPlan.objects.filter(
            user=request.user,
            date__range=[start_of_week, end_of_week]
        ).select_related('recipe')
        
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
        
        pantry_items = PantryItem.objects.filter(
            user=request.user,
            expiry_date__gte=today
        )
        
        for pantry_item in pantry_items:
            if pantry_item.ingredient.id in needed_ingredients:
                needed_ingredients[pantry_item.ingredient.id]['quantity'] -= float(pantry_item.quantity)
        
        added_count = 0
        for ing_id, data in needed_ingredients.items():
            if data['quantity'] > 0:
                exists = ShoppingListItem.objects.filter(
                    user=request.user,
                    ingredient=data['ingredient'],
                    is_purchased=False
                ).first()
                
                if exists:
                    exists.quantity += Decimal(str(data['quantity']))
                    exists.save()
                else:
                    ShoppingListItem.objects.create(
                        user=request.user,
                        ingredient=data['ingredient'],
                        quantity=Decimal(str(data['quantity']))
                    )
                added_count += 1
        
        messages.success(request, f'Список покупок сгенерирован! Добавлено {added_count} продуктов.')
        return redirect('core:shopping_list')
    
    return redirect('core:meal_plan')

@login_required(login_url='/login/')
def analytics(request):
    """Аналитика с графиками"""
    user = request.user
    
    today = date.today()
    weeks_data = []
    week_labels = []
    
    for i in range(4):
        week_start = today - timedelta(weeks=i+1)
        week_end = today - timedelta(weeks=i)
        
        purchased_items = ShoppingListItem.objects.filter(
            user=user,
            is_purchased=True,
            added_date__range=[week_start, week_end]
        ).select_related('ingredient')
        
        week_cost = sum(
            float(item.quantity) * float(item.ingredient.price_per_unit)
            for item in purchased_items
        )
        
        weeks_data.append(week_cost)
        week_labels.append(f'{week_start.strftime("%d.%m")} - {week_end.strftime("%d.%m")}')
    
    weeks_data.reverse()
    week_labels.reverse()
    
    expenses_fig = go.Figure(data=[
        go.Bar(
            x=week_labels,
            y=weeks_data,
            marker_color='#0d6efd',
            text=[f'{cost:.0f} ₽' for cost in weeks_data],
            textposition='auto'
        )
    ])
    expenses_fig.update_layout(
        title='Расходы на питание по неделям',
        xaxis_title='Неделя',
        yaxis_title='Расходы (₽)',
        template='plotly_white',
        height=400
    )
    
    expenses_graph = op.plot(expenses_fig, output_type='div', include_plotlyjs='cdn')
   
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    meal_plans = MealPlan.objects.filter(
        user=user,
        date__range=[start_of_week, end_of_week]
    ).select_related('recipe')
    
    total_protein = 0
    total_fat = 0
    total_carbs = 0
    total_calories = 0
    
    for plan in meal_plans:
        for recipe_ing in plan.recipe.ingredients.all():
            ing = recipe_ing.ingredient
            quantity_grams = float(recipe_ing.quantity) * 100
            multiplier = quantity_grams / 100
            
            total_protein += float(ing.protein) * multiplier * plan.servings_planned
            total_fat += float(ing.fat) * multiplier * plan.servings_planned
            total_carbs += float(ing.carbs) * multiplier * plan.servings_planned
            total_calories += ing.calories * multiplier * plan.servings_planned
    
    macros_fig = go.Figure(data=[
        go.Pie(
            labels=['Белки', 'Жиры', 'Углеводы'],
            values=[total_protein, total_fat, total_carbs],
            marker_colors=['#28a745', '#ffc107', '#dc3545'],
            textinfo='label+percent',
            hoverinfo='label+value'
        )
    ])
    macros_fig.update_layout(
        title=f'КБЖУ за неделю (всего {total_calories:.0f} ккал)',
        template='plotly_white',
        height=400
    )
    macros_graph = op.plot(macros_fig, output_type='div', include_plotlyjs='cdn')
    purchased_items = ShoppingListItem.objects.filter(
        user=user,
        is_purchased=True
    ).select_related('ingredient')
    
    ingredient_costs = {}
    for item in purchased_items:
        ing_name = item.ingredient.name
        cost = float(item.quantity) * float(item.ingredient.price_per_unit)
        
        if ing_name not in ingredient_costs:
            ingredient_costs[ing_name] = 0
        ingredient_costs[ing_name] += cost
    
    sorted_ingredients = sorted(ingredient_costs.items(), key=lambda x: x[1], reverse=True)[:10]
    
    top_names = [item[0] for item in sorted_ingredients]
    top_costs = [item[1] for item in sorted_ingredients]
    
    top_fig = go.Figure(data=[
        go.Bar(
            y=top_names,
            x=top_costs,
            orientation='h',
            marker_color='#17a2b8',
            text=[f'{cost:.0f} ₽' for cost in top_costs],
            textposition='auto'
        )
    ])
    top_fig.update_layout(
        title='Топ-10 продуктов по стоимости',
        xaxis_title='Стоимость (₽)',
        yaxis_title='Продукт',
        template='plotly_white',
        height=500,
        yaxis={'autorange': 'reversed'}
    )
    top_graph = op.plot(top_fig, output_type='div', include_plotlyjs='cdn')     
    
    total_spent = sum(
        float(item.quantity) * float(item.ingredient.price_per_unit)
        for item in purchased_items
    )
    
    total_items_purchased = purchased_items.count()
    
    total_meals_planned = meal_plans.count()
    
    context = {
        'expenses_graph': expenses_graph,
        'macros_graph': macros_graph,
        'top_graph': top_graph,
        'total_spent': total_spent,
        'total_items_purchased': total_items_purchased,
        'total_meals_planned': total_meals_planned,
        'total_calories': total_calories,
    }
    
    return render(request, 'core/analytics.html', context)