from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.csrf import csrf_failure

from .forms import AnswerForm, CorrectAnswerForm, QuestionForm, VoteForm
from .models import Answer, AnswerLike, Question, QuestionLike, Tag
from .pagination import paginate


def with_user_vote(objects, user):
    """Показываем уже выбранную оценку одним подзапросом для всей страницы."""
    if user.is_authenticated:
        if objects.model is Question:
            votes = QuestionLike.objects.filter(question_id=OuterRef("pk"), user=user)
        else:
            votes = AnswerLike.objects.filter(answer_id=OuterRef("pk"), user=user)
        objects = objects.annotate(user_vote=Subquery(votes.values("value")))
    return objects


def render_listing(request, template, questions, **context):
    page = paginate(with_user_vote(questions, request.user), request, per_page=4)
    return render(request, template, {**context, "questions": page.object_list, "page_obj": page})


def index(request):
    return render_listing(request, "questions/index.html", Question.objects.newest())


def hot(request):
    return render_listing(request, "questions/hot.html", Question.objects.popular())


def tag(request, tag_slug):
    selected = get_object_or_404(Tag, slug=tag_slug)
    return render_listing(request, "questions/tag.html", Question.objects.by_tag(selected.slug),
                          tag_name=selected.name)


ANSWERS_PER_PAGE = 2


def question(request, question_id):
    selected = get_object_or_404(with_user_vote(Question.objects.for_listing(), request.user),
                                 pk=question_id)
    if request.method == "POST":
        return add_answer(request, selected)
    return render_question(request, selected, AnswerForm())


def render_question(request, selected, form):
    answers = with_user_vote(Answer.objects.for_question(selected), request.user)
    page = paginate(answers, request, per_page=ANSWERS_PER_PAGE)
    return render(request, "questions/question.html", {
        "question": selected, "answers": page.object_list, "page_obj": page, "form": form,
    })


@login_required
def add_answer(request, question):
    form = AnswerForm(request.POST)
    if form.is_valid():
        answer = form.save(request.user, question)
        # Принятые ответы стоят первыми, остальные упорядочены по дате и id.
        before = question.answers.filter(Q(is_correct=True) | Q(created_at__lt=answer.created_at)
                                         | Q(created_at=answer.created_at, pk__lt=answer.pk)).count()
        number = before // ANSWERS_PER_PAGE + 1
        return redirect(f"{question.get_absolute_url()}?page={number}#answer-{answer.pk}")
    return render_question(request, question, form)


@login_required
def ask(request):
    form = QuestionForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return redirect(form.save(request.user))
    return render(request, "questions/ask.html", {"form": form})


def ajax_post(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.method != "POST":
            return JsonResponse({"error": "Требуется запрос POST."}, status=405, headers={"Allow": "POST"})
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Войдите в аккаунт и повторите действие."}, status=401)
        return view(request, *args, **kwargs)
    return wrapper


def csrf_error(request, reason=""):
    if request.path.startswith("/ajax/"):
        return JsonResponse({"error": "Обновите страницу и повторите действие."}, status=403)
    return csrf_failure(request, reason=reason)


@ajax_post
@transaction.atomic
def like_async(request, object_id, model):
    target = model.objects.select_for_update().filter(pk=object_id).first()
    if target is None:
        return JsonResponse({"error": "Запись не найдена."}, status=404)
    form = VoteForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Выберите лайк или дизлайк."}, status=400)
    try:
        rating = form.save(target, request.user)
    except ValidationError as error:
        return JsonResponse({"error": error.messages[0]}, status=409)
    return JsonResponse({"rating": rating, "value": form.cleaned_data["value"]})


@ajax_post
@transaction.atomic
def correct_async(request, question_id):
    selected = Question.objects.select_for_update().filter(pk=question_id).first()
    if selected is None:
        return JsonResponse({"error": "Вопрос не найден."}, status=404)
    if selected.author_id != request.user.pk:
        return JsonResponse({"error": "Только автор вопроса может выбрать решение."}, status=403)
    form = CorrectAnswerForm(selected, request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Выберите ответ на этот вопрос."}, status=400)
    answer = form.save()
    return JsonResponse({"answer": answer.pk, "is_correct": answer.is_correct})
