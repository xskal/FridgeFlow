from django.db import migrations
import json

def load_data(apps, schema_editor):
    Recipe = apps.get_model('core', 'Recipe')
    Ingredient = apps.get_model('core', 'Ingredient')
    RecipeIngredient = apps.get_model('core', 'RecipeIngredient')
    
    with open('fixtures.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        if item['model'] == 'core.ingredient':
            Ingredient.objects.create(**item['fields'])
        elif item['model'] == 'core.recipe':
            Recipe.objects.create(**item['fields'])
        elif item['model'] == 'core.recipeingredient':
            RecipeIngredient.objects.create(**item['fields'])

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_data),
    ]