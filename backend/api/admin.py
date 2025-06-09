from django.contrib import admin
from .models import MyUser, Tag, Ingredient, Recipe, RecipeIngredient


@admin.register(MyUser)
class MyUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'is_active'
    )
    search_fields = ('email', 'username')
    list_filter = ('is_active',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__email', 'author__username')
    list_filter = ('tags',)
    inlines = [RecipeIngredientInline]

    def favorites_count(self, obj):
        return getattr(
            obj,
            'favorites',
            []).count() if hasattr(
                obj,
                'favorites'
        ) else 0
    favorites_count.short_description = 'В избранном'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
