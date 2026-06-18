from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.recipe_list, name='recipe_list'),
    path('recipe/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Холодильник
    path('pantry/', views.pantry_list, name='pantry_list'),
    path('pantry/add/', views.pantry_add, name='pantry_add'),
    path('pantry/edit/<int:pk>/', views.pantry_edit, name='pantry_edit'),
    path('pantry/delete/<int:pk>/', views.pantry_delete, name='pantry_delete'),

    # Список покупок
    path('shopping/', views.shopping_list, name='shopping_list'),
    path('shopping/add/', views.shopping_add, name='shopping_add'),
    path('shopping/toggle/<int:pk>/', views.shopping_toggle, name='shopping_toggle'),
    path('shopping/delete/<int:pk>/', views.shopping_delete, name='shopping_delete'),
    path('shopping/generate/', views.shopping_generate, name='shopping_generate'),
    path('shopping/clear/', views.shopping_clear_purchased, name='shopping_clear_purchased'),

    # Планирование питания
    path('meal-plan/', views.meal_plan, name='meal_plan'),
    path('meal-plan/add/', views.meal_plan_add, name='meal_plan_add'),
    path('meal-plan/delete/<int:pk>/', views.meal_plan_delete, name='meal_plan_delete'),
    path('meal-plan/generate/', views.meal_plan_generate_shopping, name='meal_plan_generate_shopping'),
]