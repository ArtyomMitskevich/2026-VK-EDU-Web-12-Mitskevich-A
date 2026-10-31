from django.shortcuts import render


def login(request):
    """В ДЗ2 отображаем форму, без проверки пароля."""
    return render(request, 'core/login.html')


def signup(request):
    return render(request, 'core/signup.html')


def profile(request):
    return render(request, 'core/profile.html')
