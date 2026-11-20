from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import Profile


class AccountTests(TestCase):
    def test_signup_password_validation_and_profile(self):
        fields = dict(username="student", email="mail@example.org", first_name="Иван",
                      password1="123", password2="123")
        response = self.client.post("/signup/", fields)
        self.assertTrue(response.context["form"].errors["password2"])
        self.assertFalse(User.objects.exists())
        fields.update(password1="A-good-password-95", password2="A-good-password-95")
        self.assertRedirects(self.client.post("/signup/", fields), "/")
        self.assertEqual(Profile.objects.get().user.username, "student")

    def test_return_after_login_and_logout(self):
        User.objects.create_user("student", password="StrongPass456")
        for target, expected in [("/hot/?page=2", "/hot/?page=2"), ("https://example.org/", "/")]:
            response = self.client.post("/login/", {"username": "student", "password": "StrongPass456",
                                                    "next": target})
            self.assertRedirects(response, expected)
            self.assertRedirects(self.client.post("/logout/", {"next": "/hot/"}), "/hot/")

    def test_login_and_logout_accept_relative_urls(self):
        User.objects.create_user("student", password="StrongPass456")
        login = self.client.post("/login/?next=%3Fpage%3D2", {
            "username": "student", "password": "StrongPass456",
        })
        self.assertEqual(login.status_code, 302)
        self.assertEqual(login["Location"], "?page=2")
        logout = self.client.post("/logout/", {"next": "#answers"})
        self.assertEqual(logout.status_code, 302)
        self.assertEqual(logout["Location"], "#answers")

    def test_profile_image(self):
        self.client.force_login(User.objects.create_user("student"))
        data = {"username": "newnick", "email": "test@example.org"}
        image = BytesIO()
        Image.new("RGB", (8, 8)).save(image, "PNG")
        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            invalid = SimpleUploadedFile("photo.txt", image.getvalue())
            response = self.client.post("/profile/", {**data, "avatar": invalid})
            self.assertFormError(response.context["form"], "avatar", "Выберите файл JPEG, PNG или WebP.")
            upload = SimpleUploadedFile("photo.png", image.getvalue(), content_type="image/png")
            self.assertRedirects(self.client.post("/profile/", {**data, "avatar": upload}), "/profile/")
            profile = Profile.objects.get(user__username="newnick")
            self.assertRegex(profile.avatar.name, r"^avatars/[0-9a-f]{32}\.png$")
            self.assertTrue(profile.avatar.storage.exists(profile.avatar.name))

    def test_profile_form_prefills_saved_user_data(self):
        user = User.objects.create_user("student", email="student@example.org")
        self.client.force_login(user)
        form = self.client.get("/profile/").context["form"]
        self.assertFalse(form.is_bound)
        self.assertEqual(form["username"].value(), user.username)
        self.assertEqual(form["email"].value(), user.email)
