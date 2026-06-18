from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient, MealPlan, PantryItem, ShoppingListItem

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_per_unit', 'unit')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooking_time', 'difficulty', 'servings')
    list_filter = ('difficulty',)
    search_fields = ('name', 'description')

@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'quantity')
    list_filter = ('recipe',)
    search_fields = ('ingredient__name',)

@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'meal_type', 'recipe')
    list_filter = ('meal_type', 'date')
    search_fields = ('recipe__name',)

@admin.register(PantryItem)
class PantryItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingredient', 'quantity', 'expiry_date')
    list_filter = ('expiry_date',)
    search_fields = ('ingredient__name',)

@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingredient', 'quantity', 'is_purchased', 'added_date')
    list_filter = ('is_purchased',)
    search_fields = ('ingredient__name',)