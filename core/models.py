from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Дополнительные данные встроенного пользователя Django."""

    # У пользователя может быть только один профиль. При удалении пользователя
    # Django удалит и запись профиля.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="пользователь",
    )
    # В базе хранится путь к загруженному файлу. Аватар можно не указывать.
    avatar = models.FileField("аватар", upload_to="avatars/", blank=True)

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        return f"Профиль №{self.pk}"
