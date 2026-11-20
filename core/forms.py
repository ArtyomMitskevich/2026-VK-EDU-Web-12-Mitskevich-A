from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

from .models import Profile, validate_avatar


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта")
    first_name = forms.CharField(label="Имя", max_length=150)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name")

    @transaction.atomic
    def save(self):
        # Аккаунт и профиль создаются вместе после проверки пароля.
        user = super().save()
        Profile.objects.create(user=user)
        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(label="Электронная почта")

    class Meta:
        model = User
        fields = ("username", "email")
        labels = {"username": "Ник"}

    avatar = forms.ImageField(label="Аватар", required=False,
                              help_text="JPEG, PNG или WebP до 5 МБ.")

    def clean_avatar(self):
        image = self.cleaned_data.get("avatar")
        if image:
            validate_avatar(image)
            if image.image.format not in {"JPEG", "PNG", "WEBP"}:
                raise forms.ValidationError("Выберите изображение JPEG, PNG или WebP.")
        return image

    @transaction.atomic
    def save(self):
        user = super().save()
        profile, _ = Profile.objects.get_or_create(user=user)
        if self.cleaned_data["avatar"]:
            profile.avatar = self.cleaned_data["avatar"]
            profile.save(update_fields=["avatar"])
        return user
