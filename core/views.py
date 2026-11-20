from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ProfileForm, RegisterForm


def next_url(request):
    target = request.POST.get("next", request.GET.get("next", ""))
    if url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse("index")


def login(request):
    form = AuthenticationForm(request, data=request.POST if request.method == "POST" else None)
    target = next_url(request)
    if request.method == "POST" and form.is_valid():
        auth.login(request, form.get_user())
        return redirect(target)
    return render(request, "core/login.html", {"form": form, "next": target})


def signup(request):
    form = RegisterForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        auth.login(request, form.save())
        return redirect("index")
    return render(request, "core/signup.html", {"form": form})


@login_required
def profile(request):
    form = ProfileForm(request.POST if request.method == "POST" else None,
                       request.FILES, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("profile")
    return render(request, "core/profile.html", {"form": form})


@require_POST
def logout(request):
    target = next_url(request)
    auth.logout(request)
    return redirect(target)
