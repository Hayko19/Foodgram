from django.contrib import admin

from users.models import MyUser


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
