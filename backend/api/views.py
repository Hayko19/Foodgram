from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Subscription, Tag)
from users.models import MyUser

from .filters import IngredientFilter, RecipeFilter
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer, UserAvatarSerializer,
                          UserCreateSerializer, UserListSerializer)


def short_link_redirect(request, short_code):
    recipe = get_object_or_404(Recipe, short_uuid=short_code)
    return redirect(f'/recipes/{recipe.id}/')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра ингредиентов.
    Позволяет получать список и детали ингредиентов.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserAvatarUpdateView(generics.UpdateAPIView):
    """
    View для обновления аватара пользователя.
    Позволяет пользователю загрузить новый аватар.
    """
    serializer_class = UserAvatarSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    Позволяет создавать, просматривать и редактировать пользователей,
    """
    queryset = MyUser.objects.all()
    serializer_class = UserListSerializer
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserListSerializer

    @action(
        detail=False,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not user.check_password(current_password):
            return Response(
                {'current_password': 'Неверный текущий пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not new_password:
            return Response(
                {'new_password': 'Новый пароль обязателен.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscriptionSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = self.get_object()
        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SubscriptionSerializer(
                subscription,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user,
                author=author
            ).delete()
            if deleted == 0:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с тегами.
    Позволяет получать список тегов и их детали.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления рецептами.
    Позволяет создавать, просматривать, редактировать и удалять рецепты.
    Также поддерживает действия для избранного и списка покупок.
    """
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'ingredients', 'tags', 'recipe_ingredients__ingredient'
    )
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeSerializer

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Вы не можете удалять чужие рецепты.'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {'detail': 'Вы не можете редактировать чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        url = request.build_absolute_uri(f'/api/s/{recipe.short_uuid}/')
        return Response({"short-link": url})

    def _add_to(self, request, pk, model, serializer_class, error_message):
        recipe = self.get_object()
        user = request.user
        obj, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            return Response(
                {'detail': error_message['already']},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = serializer_class(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from(self, request, pk, model, error_message):
        recipe = self.get_object()
        user = request.user
        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if deleted == 0:
            return Response(
                {'detail': error_message['not_found']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        error_message = {
            'already': 'Рецепт уже в списке покупок',
            'not_found': 'Рецепт не найден в списке покупок'
        }
        if request.method == 'POST':
            return self._add_to(
                request,
                pk,
                ShoppingCart,
                ShoppingCartSerializer,
                error_message
            )
        elif request.method == 'DELETE':
            return self._remove_from(request, pk, ShoppingCart, error_message)

    @action(
        detail=True, methods=('post', 'delete'),
        permission_classes=(permissions.IsAuthenticated,),
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        error_message = {
            'already': 'Рецепт уже в избранном',
            'not_found': 'Рецепт не найден в избранном'
        }
        if request.method == 'POST':
            return self._add_to(
                request,
                pk,
                Favorite,
                FavoriteSerializer,
                error_message
            )
        elif request.method == 'DELETE':
            return self._remove_from(request, pk, Favorite, error_message)

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in_cart__user=user)
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit')
            )
            .annotate(amount=Sum('amount'))
            .order_by('name')
        )
        lines = [
            f'{item["name"]}. Единица измерения: {item["unit"]}, '
            f'количество: {item["amount"]}.'
            for item in ingredients
        ]
        content = "\n".join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
