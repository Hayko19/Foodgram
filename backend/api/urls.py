from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    UserAvatarUpdateView, UserViewSet, short_link_redirect)

router_v1 = DefaultRouter()
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'users', UserViewSet, basename='users')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = router_v1.urls

urlpatterns += [
    path(
        'users/me/avatar/',
        UserAvatarUpdateView.as_view(),
        name='user-avatar-upload'
    ),
    path(
        's/<str:short_code>/',
        short_link_redirect,
        name='short-link-redirect'
    ),
]
