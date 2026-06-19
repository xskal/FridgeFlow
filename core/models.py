from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Ingredient(models.Model):
    CATEGORY_CHOICES = [
        ('vegetables', 'Овощи и зелень'),
        ('fruits', 'Фрукты и ягоды'),
        ('meat', 'Мясо и птица'),
        ('dairy', 'Молочные продукты'),
        ('grocery', 'Бакалея и крупы'),
        ('spices', 'Специи и соусы'),
        ('other', 'Другое'),
    ]
    
    UNIT_CHOICES = [
        ('kg', 'кг'),
        ('g', 'г'),
        ('l', 'л'),
        ('ml', 'мл'),
        ('pcs', 'шт'),
        ('pack', 'уп'),
    ]

    name = models.CharField('Название продукта', max_length=200)
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES)
    unit = models.CharField('Единица измерения', max_length=10, choices=UNIT_CHOICES)
    price_per_unit = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2, default=0)
    
    calories = models.IntegerField('Ккал на 100г', default=0)
    protein = models.DecimalField('Белки на 100г', max_digits=5, decimal_places=2, default=0)
    fat = models.DecimalField('Жиры на 100г', max_digits=5, decimal_places=2, default=0)
    carbs = models.DecimalField('Углеводы на 100г', max_digits=5, decimal_places=2, default=0)
    
    shelf_life_days = models.IntegerField('Срок хранения (дней)', default=7)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легко'),
        ('medium', 'Средне'),
        ('hard', 'Сложно'),
    ]

    name = models.CharField('Название блюда', max_length=200)
    description = models.TextField('Краткое описание', blank=True)
    cooking_time = models.IntegerField('Время готовки (мин)', default=30)
    servings = models.IntegerField('Количество порций', default=2)
    difficulty = models.CharField('Сложность', max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    instructions = models.TextField('Пошаговая инструкция')
    image = models.ImageField('Изображение', upload_to='recipes/', blank=True, null=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients', verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='used_in_recipes', verbose_name='Продукт')
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f"{self.ingredient.name} для {self.recipe.name}"


class MealPlan(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('snack', 'Перекус'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans', verbose_name='Пользователь')
    date = models.DateField('Дата')
    meal_type = models.CharField('Прием пищи', max_length=10, choices=MEAL_TYPE_CHOICES)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='meal_plans', verbose_name='Блюдо')
    servings_planned = models.IntegerField('Порций к готовке', default=1)

    class Meta:
        verbose_name = 'Запись в плане питания'
        verbose_name_plural = 'План питания'
        ordering = ['date', 'meal_type']
        unique_together = ('user', 'date', 'meal_type') # Нельзя два обеда в один день

    def __str__(self):
        return f"{self.get_meal_type_display()} - {self.date} ({self.recipe.name})"


class PantryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pantry_items', verbose_name='Пользователь')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='pantry_items', verbose_name='Продукт')
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    purchase_date = models.DateField('Дата покупки', auto_now_add=True)
    expiry_date = models.DateField('Срок годности')

    class Meta:
        verbose_name = 'Продукт в холодильнике'
        verbose_name_plural = 'Холодильник'

    def __str__(self):
        return f"{self.ingredient.name} ({self.quantity})"


class ShoppingListItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_list', verbose_name='Пользователь')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='shopping_items', verbose_name='Продукт')
    quantity = models.DecimalField('Количество', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_purchased = models.BooleanField('Куплено', default=False)
    added_date = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Пункт списка покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ['-added_date']

    def __str__(self):
        status = "✅" if self.is_purchased else "⬜"
        return f"{status} {self.ingredient.name} ({self.quantity})"