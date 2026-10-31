from django.contrib import admin
from django.urls import include, path

# Корневой URLconf распределяет запросы между приложениями.
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('questions.urls')),
    path('', include('core.urls')),
]
