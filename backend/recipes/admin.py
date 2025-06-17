from django.contrib import admin
from django.utils.safestring import mark_safe
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description='Использовано в рецептах')
    def recipes_count(self, obj):
        return RecipeIngredient.objects.filter(ingredient=obj).count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cooking_time_with_unit',
        'author',
        'tags_html',
        'ingredients_html',
        'image_tag',
        'favorites_count'
    )
    search_fields = ('name', 'author__email', 'author__username', 'tags__name')
    list_filter = ('author', 'tags')
    inlines = [RecipeIngredientInline]

    @admin.display(description='Время готовки (мин)')
    def cooking_time_with_unit(self, obj):
        return f'{obj.cooking_time} мин'

    @admin.display(description='Теги')
    @mark_safe
    def tags_html(self, obj):
        return '<br>'.join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_html(self, obj):
        return '<br>'.join([
            f'{ri.ingredient.name}'
            f'({ri.amount} {ri.ingredient.measurement_unit})'
            for ri in obj.recipe_ingredients.all()
        ])

    @admin.display(description='Картинка')
    @mark_safe
    def image_tag(self, obj):
        if obj.image:
            return (
                f'<img src="{obj.image.url}"'
                f'style="max-height:60px;max-width:60px;" />'
            )
        return '-'

    @admin.display(description='В избранном')
    def favorites_count(self, obj):
        return obj.favorites.count() if hasattr(obj, 'favorites') else 0


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
