from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile


class ProfileInline(admin.StackedInline):
    """Профиль редактируется вместе с учётной записью пользователя."""

    model = Profile
    extra = 0
    max_num = 1


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar")
    search_fields = ("user__username", "user__email")
    list_filter = (("avatar", admin.EmptyFieldListFilter),)
    list_select_related = ("user",)
    autocomplete_fields = ("user",)


# Стандартная админка пользователя сохраняет управление паролями и правами.
User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = (ProfileInline,)


admin.site.site_header = "Управление сайтом «Точка сборки»"
admin.site.site_title = "Точка сборки"
admin.site.index_title = "Управление данными"
