from django.conf import settings
from django.db import models
from django.db.models import Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.urls import reverse


class Tag(models.Model):
    """Название показываем в интерфейсе, slug используем в адресе страницы тега."""

    name = models.CharField("название", max_length=50, unique=True)
    slug = models.SlugField("код для URL", max_length=60, unique=True)

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name

    @property
    def color(self):
        """У тега один цвет в карточках и боковой колонке."""
        palette = ("blue", "sage", "sand", "teal", "lavender", "rose")
        return palette[(self.pk or 0) % len(palette)]


class QuestionManager(models.Manager):
    """Готовые выборки для главной, популярных вопросов и страниц тегов."""

    def for_listing(self):
        """Загружаем авторов и теги заранее для карточек списка."""
        # Автор и профиль загружаются вместе с вопросами, теги — одним отдельным
        # запросом на весь список.
        # Независимые подзапросы не перемножают голоса и ответы при подсчёте.
        votes = QuestionLike.objects.filter(question_id=OuterRef("pk")).values("question_id")
        answers = Answer.objects.filter(question_id=OuterRef("pk")).values("question_id")
        return (
            self.select_related("author", "author__profile")
            .prefetch_related("tags")
            .annotate(
                rating=Coalesce(Subquery(votes.annotate(total=Sum("value")).values("total")), 0),
                answer_count=Coalesce(Subquery(answers.annotate(total=Count("pk")).values("total")), 0),
            )
        )

    def newest(self):
        return self.for_listing().order_by("-created_at", "-pk")

    def popular(self):
        # Суммируем лайки и дизлайки в БД. У вопроса без оценок рейтинг равен нулю.
        return self.for_listing().order_by("-rating", "-created_at", "-pk")

    def by_tag(self, slug):
        return self.newest().filter(tags__slug=slug)


class Question(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="questions", verbose_name="автор",
    )
    title = models.CharField("заголовок", max_length=200)
    text = models.TextField("текст")
    created_at = models.DateTimeField("дата публикации", auto_now_add=True, db_index=True)
    # Один вопрос может иметь несколько тегов, и каждый тег можно использовать повторно.
    tags = models.ManyToManyField(Tag, related_name="questions", blank=True, verbose_name="теги")

    objects = QuestionManager()

    class Meta:
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Строим адрес вопроса по имени маршрута и ID."""
        return reverse("question", kwargs={"question_id": self.pk})


class AnswerManager(models.Manager):
    def for_question(self, question):
        votes = AnswerLike.objects.filter(answer_id=OuterRef("pk")).values("answer_id")
        return (
            self.filter(question=question)
            .select_related("author", "author__profile")
            .annotate(rating=Coalesce(Subquery(votes.annotate(total=Sum("value")).values("total")), 0))
            .order_by("-is_correct", "created_at", "pk")
        )


class Answer(models.Model):
    """Ответ на конкретный вопрос. Автор вопроса может отметить его как решение."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers", verbose_name="вопрос",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="answers", verbose_name="автор",
    )
    text = models.TextField("текст")
    created_at = models.DateTimeField("дата публикации", auto_now_add=True)
    is_correct = models.BooleanField("принят как решение", default=False)

    objects = AnswerManager()

    class Meta:
        verbose_name = "ответ"
        verbose_name_plural = "ответы"

    def __str__(self):
        return f"Ответ №{self.pk}"


class VoteValue(models.IntegerChoices):
    """Значения оценок, из которых складывается рейтинг."""

    DOWN = -1, "Дизлайк"
    UP = 1, "Лайк"


class QuestionLike(models.Model):
    """Голос пользователя за вопрос."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="пользователь",
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="likes", verbose_name="вопрос",
    )
    value = models.SmallIntegerField("оценка", choices=VoteValue.choices)

    class Meta:
        verbose_name = "оценка вопроса"
        verbose_name_plural = "оценки вопросов"
        # Один пользователь может оценить конкретный вопрос только один раз.
        unique_together = (("user", "question"),)
        # База принимает только значения −1 и +1.
        constraints = [
            models.CheckConstraint(condition=models.Q(value__in=[-1, 1]), name="question_vote_value"),
        ]


class AnswerLike(models.Model):
    """Голос пользователя за ответ с теми же ограничениями, что и у оценки вопроса."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="пользователь",
    )
    answer = models.ForeignKey(
        Answer, on_delete=models.CASCADE, related_name="likes", verbose_name="ответ",
    )
    value = models.SmallIntegerField("оценка", choices=VoteValue.choices)

    class Meta:
        verbose_name = "оценка ответа"
        verbose_name_plural = "оценки ответов"
        unique_together = (("user", "answer"),)
        constraints = [
            models.CheckConstraint(condition=models.Q(value__in=[-1, 1]), name="answer_vote_value"),
        ]
