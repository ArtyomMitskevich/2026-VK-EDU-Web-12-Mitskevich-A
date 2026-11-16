from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import Tag


def sidebar(request):
    """Подборки для общей боковой колонки, по одной выборке на блок."""
    tags = Tag.objects.annotate(question_count=Count("questions")).filter(question_count__gt=0)
    members = (
        get_user_model().objects.select_related("profile")
        .annotate(answer_count=Count("answers")).filter(answer_count__gt=0)
    )
    return {
        "popular_tags": tags.order_by("-question_count", "pk")[:6],
        "best_members": members.order_by("-answer_count", "pk")[:3],
    }
