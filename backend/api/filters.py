from django_filters import rest_framework as filters

from recipes.models import Recipe
from recipes.models import Tag, Ingredient


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов.
    Позволяет фильтровать рецепты по автору, тегам,
    наличию в списке покупок и избранном.
    """
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user is not None and user.is_authenticated and value:
            return queryset.filter(in_cart__user=user)
        if value is False:
            return queryset.exclude(in_cart__user=user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, 'user', None)
        if user is not None and user.is_authenticated and value:
            return queryset.filter(favorited_by__user=user)
        if value is False:
            return queryset.exclude(favorited_by__user=user)
        return queryset


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
