from django.http import Http404
from django.shortcuts import render

# Временный источник данных, который позже заменим запросами к базе.
from .data import ANSWERS, QUESTIONS, TAGS
from .pagination import paginate



def index(request):
    """Главная страница: передаём вопросы из Python в шаблон."""
    # render находит шаблон в questions/templates и возвращает готовую страницу.
    page = paginate(QUESTIONS, request, per_page=4)
    return render(request, "questions/index.html", {"questions": page.object_list, "page_obj": page})


def hot(request):
    """Популярные вопросы: сортируем данные по рейтингу."""
    ordered = sorted(QUESTIONS, key=lambda q: q["rating"], reverse=True)
    page = paginate(ordered, request, per_page=4)
    return render(request, "questions/hot.html", {"questions": page.object_list, "page_obj": page})


def question(request, question_id):
    """Находим данные вопроса по номеру из адреса страницы."""
    # next возвращает первый подходящий словарь или None, если вопроса нет.
    selected = next((item for item in QUESTIONS if item["id"] == question_id), None)
    if selected is None:
        raise Http404("Такого вопроса нет")
    page = paginate(ANSWERS[selected['id']], request, per_page=2)
    return render(request, "questions/question.html", {
        "question": selected, "answers": page.object_list, "page_obj": page,
    })


def tag(request, tag_slug):
    """Фильтруем вопросы по тегу из адреса."""
    if tag_slug not in TAGS:
        raise Http404("Такого тега нет")
    selected = [q for q in QUESTIONS if any(t['slug'] == tag_slug for t in q['tags'])]
    page = paginate(selected, request, per_page=4)
    return render(request, 'questions/tag.html', {
        'questions': page.object_list, 'page_obj': page, 'tag_name': TAGS[tag_slug],
    })


def ask(request):
    return render(request, 'questions/ask.html')
