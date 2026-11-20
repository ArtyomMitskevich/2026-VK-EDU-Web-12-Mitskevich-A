from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


def avatar_path(instance, filename):
    return f"avatars/{uuid4().hex}{Path(filename).suffix.lower()}"


def validate_avatar(file):
    FileExtensionValidator(["jpg", "jpeg", "png", "webp"])(file)
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Размер аватара должен быть не больше 5 МБ.")


class Profile(models.Model):
    """Дополнительные данные встроенного пользователя Django."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="profile", verbose_name="пользователь",
    )
    avatar = models.ImageField("аватар", upload_to=avatar_path, blank=True,
                               validators=[validate_avatar])

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        return f"Профиль №{self.pk}"
