from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import MAX_LENGTH_USERNAME


def user_avatar_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'


class MyUser(AbstractUser):
    first_name = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
        help_text="Имя",
        verbose_name="Имя"
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_USERNAME,
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

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['email']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Subscription(models.Model):
    user = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
