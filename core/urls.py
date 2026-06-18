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
]