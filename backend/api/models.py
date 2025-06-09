import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


def user_avatar_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'


class MyUser(AbstractUser):
    first_name = models.CharField(
        max_length=150,
        help_text="Имя",
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=150,
        help_text="Фамилия",
        verbose_name="Фамилия"
    )
    email = models.EmailField(
        unique=True,
        help_text="Адрес электронной почты",
        verbose_name="Адрес электронной почты"
    )
    avatar = models.ImageField(
        upload_to='users/image',
        blank=True,
        null=True,
        default='users/default.jpg',
        verbose_name="Аватар пользователя",
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['email']


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Название тега",
        verbose_name="Название тега"
    )
    slug = models.SlugField(unique=True, verbose_name="Слаг",)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Название ингредиента",
        verbose_name="Название ингредиента"
    )
    measurement_unit = models.CharField(
        max_length=50,
        help_text="Единица измерения",
        verbose_name="Единица измерения"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']


class Recipe(models.Model):
    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=100,
        help_text="Название рецепта",
        verbose_name="Название рецепта"
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        help_text="Изображение рецепта"
    )
    text = models.TextField(
        help_text="Описание",
        verbose_name="Описание"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name="Ингредиенты",
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name="Теги",
    )
    cooking_time = models.PositiveIntegerField(
        help_text="Время приготовления (в минутах)",
        verbose_name="Время приготовления (минуты)"
    )
    short_uuid = models.CharField(max_length=10, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.short_uuid:
            self.short_uuid = uuid.uuid4().hex[:6]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ['name']


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент"
    )
    amount = models.PositiveIntegerField(
        verbose_name="Количество"
    )

    class Meta:
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_cart',
        verbose_name="Рецепт"
    )

    class Meta:
        verbose_name = "Корзина покупок"
        verbose_name_plural = "Корзины покупок"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe_in_cart'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    class Meta:
        unique_together = ('user', 'recipe')


class Subscription(models.Model):
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name="Автор"
    )

    class Meta:
        unique_together = ('user', 'author')
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
