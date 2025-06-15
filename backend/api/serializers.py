from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import MyUser, Subscription
from .constants import DEFAULT_RECIPES_LIMIT


class RecipeShortSerializer(serializers.ModelSerializer):
    """
    Сериализатор для краткого отображения рецепта.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания пользователя.
    Он используется для регистрации нового пользователя.
    """
    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = MyUser.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
        )
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели MyUser.
    Он используется для отображения информации о пользователе.
    """
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = MyUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            url = obj.avatar.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None


class UserAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = MyUser
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Tag.
    Он используется для отображения информации о тегах.
    """
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели RecipeIngredient.
    Он используется для отображения информации об ингредиентах в рецепте.
    Он включает в себя поля для идентификатора, названия, единицы измерения
    и количества ингредиента.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Recipe.
    Он используется для отображения информации о рецепте.
    Он включает в себя теги, автора, ингредиенты и поля для избранного
    и корзины покупок.
    """
    tags = TagSerializer(many=True, read_only=True)
    author = UserListSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество должно быть больше 0.'
            )
        return value


class RecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Recipe.
    Он используется для создания и обновления рецептов.
    Он также включает в себя валидацию ингредиентов и тегов.
    """
    ingredients = IngredientAmountSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True
    )
    image = Base64ImageField()
    author = UserListSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise ValidationError(
                {'ingredients': 'Поле ingredients обязательно при обновлении.'}
            )
        if 'tags' not in validated_data:
            raise ValidationError(
                {'tags': 'Поле tags обязательно при обновлении.'}
            )
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        recipe_ingredients = [
            RecipeIngredient(
                recipe=instance,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return instance

    def validate_cooking_time(self, value):
        if value <= 0:
            raise ValidationError({
                "cooking_time": (
                    "Время приготовления должно быть больше нуля."
                )
            })
        return value

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(
                {"ingredients": "Список ингредиентов не может быть пустым."}
            )
        seen_ids = set()
        for ingredient in value:
            ingredient_id = ingredient['id']
            if ingredient_id in seen_ids:
                raise ValidationError({
                    "ingredients": (
                        f"Ингредиент с id {ingredient_id} "
                        "указан несколько раз."
                    )
                })
            seen_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError(
                {"tags": "Список тегов не может быть пустым."}
            )
        seen_ids = set()
        for tag in value:
            tag_id = tag.id
            if tag_id in seen_ids:
                raise ValidationError({
                    "tags": (
                        f"Тег с id {tag_id} "
                        "указан несколько раз."
                    )
                })
            seen_ids.add(tag_id)
        return value

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()

    def to_representation(self, instance):

        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели ShoppingCart.
    Он используется для отображения информации о рецептах в корзине покупок.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Favorite.
    Он используется для отображения информации о рецептах в избранном.
    """
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Subscription.
    Он используется для отображения информации о подписках пользователя.
    """
    email = serializers.EmailField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(
        source='author.first_name',
        read_only=True
    )
    last_name = serializers.CharField(
        source='author.last_name',
        read_only=True
    )
    avatar = serializers.ImageField(
        source='author.avatar',
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_qs = obj.author.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None and recipes_limit.isdigit():
            recipes_qs = recipes_qs[:int(recipes_limit)]
        else:
            recipes_qs = recipes_qs[:DEFAULT_RECIPES_LIMIT]
        serializer = RecipeShortSerializer(
            recipes_qs,
            many=True,
            context=self.context
        )
        return serializer.data


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient.
    """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
