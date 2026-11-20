from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from core.models import Profile
from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class PageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user("engineer")
        Profile.objects.create(user=cls.author)
        cls.tag = Tag.objects.create(name="Электроника", slug="electronics")
        cls.empty_tag = Tag.objects.create(name="САПР", slug="cad")
        cls.question = Question.objects.create(author=cls.author, title="LM7805", text="Текст")
        cls.question.tags.add(cls.tag)
        for i in range(3):
            Answer.objects.create(question=cls.question, author=cls.author, text=f"Ответ {i}")
        QuestionLike.objects.create(question=cls.question, user=cls.author, value=1)

    def test_routes(self):
        for name in ("index", "hot", "login", "signup"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_private_routes(self):
        for name in ("ask", "profile"):
            url = reverse(name)
            self.assertRedirects(self.client.get(url), f"/login/?next={url}")
        self.client.force_login(self.author)
        for name in ("ask", "profile"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_question_ranking_and_independent_answer_count(self):
        newest = Question.objects.create(author=self.author, title="Новый", text="Текст")
        self.assertEqual(self.client.get("/").context["questions"][0], newest)
        highest = self.client.get("/hot/").context["questions"][0]
        self.assertEqual(highest, self.question)
        self.assertEqual((highest.rating, highest.answer_count), (1, 3))

    def test_tag_filters_and_empty_tag(self):
        Question.objects.create(author=self.author, title="Без тегов", text="Текст")
        response = self.client.get("/tag/electronics/")
        self.assertEqual(list(response.context["questions"]), [self.question])
        self.assertContains(self.client.get("/tag/cad/"), "Вопросов по этому тегу пока нет.")

    def test_unknown_objects(self):
        for path in ("/question/999/", "/question/abc/", "/tag/unknown/"):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_pagination(self):
        for i in range(4):
            Question.objects.create(author=self.author, title=f"Вопрос {i}", text="Текст")
        self.assertEqual(len(self.client.get("/?page=1").context["questions"]), 4)
        self.assertEqual(len(self.client.get("/?page=2").context["questions"]), 1)
        for value in ("abc", "0", "-1", "9999", "1.5", ""):
            self.assertEqual(self.client.get("/", {"page": value}).context["page_obj"].number, 1)
        response = self.client.get(self.question.get_absolute_url(), {"page": 2})
        self.assertEqual(len(response.context["answers"]), 1)

    def test_empty_pages_and_question_without_tags(self):
        question = Question.objects.create(author=self.author, title="Без тегов", text="Текст")
        self.assertContains(self.client.get(question.get_absolute_url()), "Ответов пока нет")
        Question.objects.all().delete()
        self.assertContains(self.client.get("/"), "Пока нет ни одного вопроса")

    def test_queries_do_not_grow_with_cards(self):
        with CaptureQueriesContext(connection) as single:
            self.client.get("/")
        for i in range(3):
            author = get_user_model().objects.create_user(f"author{i}")
            question = Question.objects.create(author=author, title=f"Вопрос {i}", text="Текст")
            question.tags.add(self.tag)
        with CaptureQueriesContext(connection) as several:
            self.client.get("/")
        self.assertEqual(len(single), len(several))

    def test_duplicate_vote_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            QuestionLike.objects.create(question=self.question, user=self.author, value=-1)


class FillDbTests(TestCase):
    def test_exact_counts_and_repeat_run(self):
        for runs in (1, 2):
            call_command("fill_db", 2, stdout=StringIO())
            self.assertEqual(get_user_model().objects.count(), runs * 2)
            self.assertEqual(Profile.objects.count(), runs * 2)
            self.assertEqual(Tag.objects.count(), runs * 2)
            self.assertEqual(Question.objects.count(), runs * 20)
            self.assertEqual(Answer.objects.count(), runs * 200)
            self.assertEqual(QuestionLike.objects.count() + AnswerLike.objects.count(), runs * 400)


class AdminAnswerTests(TestCase):
    def test_inline_creates_answer_as_current_admin(self):
        admin = get_user_model().objects.create_superuser("editor")
        self.client.force_login(admin)
        question = Question.objects.create(author=admin, title="Вопрос", text="Описание")
        url = reverse("admin:questions_question_change", args=[question.pk])
        response = self.client.post(url, {
            "author": admin.pk,
            "title": question.title,
            "text": question.text,
            "answers-TOTAL_FORMS": "1",
            "answers-INITIAL_FORMS": "0",
            "answers-MIN_NUM_FORMS": "0",
            "answers-MAX_NUM_FORMS": "1000",
            "answers-0-text": "Ответ из админки",
            "_save": "Сохранить",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(question.answers.get().author, admin)
