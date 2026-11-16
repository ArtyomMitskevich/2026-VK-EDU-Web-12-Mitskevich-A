from django.shortcuts import get_object_or_404, render

from .models import Answer, Question, Tag
from .pagination import paginate


def render_listing(request, template, questions, **context):
    """Одинаковая пагинация для трёх списков вопросов."""
    page = paginate(questions, request, per_page=4)
    return render(request, template, {**context, "questions": page.object_list, "page_obj": page})


def index(request):
    return render_listing(request, "questions/index.html", Question.objects.newest())


def hot(request):
    return render_listing(request, "questions/hot.html", Question.objects.popular())


def tag(request, tag_slug):
    selected = get_object_or_404(Tag, slug=tag_slug)
    return render_listing(
        request, "questions/tag.html", Question.objects.by_tag(selected.slug), tag_name=selected.name,
    )


def question(request, question_id):
    selected = get_object_or_404(Question.objects.for_listing(), pk=question_id)
    page = paginate(Answer.objects.for_question(selected), request, per_page=2)
    return render(request, "questions/question.html", {
        "question": selected, "answers": page.object_list, "page_obj": page,
    })


def ask(request):
    return render(request, "questions/ask.html")
