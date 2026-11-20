from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Answer, Question


class PublicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user("author")
        cls.reader = User.objects.create_user("reader")
        cls.question = Question.objects.create(author=cls.author, title="Вопрос", text="Описание")

    def test_question_and_paginated_answer(self):
        self.client.force_login(self.reader)
        response = self.client.post("/ask/", {"title": "Django", "text": "Как сохранить форму?",
                                               "tag_names": "Python, базы, python"})
        question = Question.objects.get(title="Django")
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(question.tags.count(), 2)
        for i in range(2):
            Answer.objects.create(author=self.author, question=question, text=str(i))
        response = self.client.post(question.get_absolute_url(), {"text": "Через save()."})
        answer = Answer.objects.get(text="Через save().")
        self.assertEqual(response.url, f"{question.get_absolute_url()}?page=2#answer-{answer.pk}")
        self.assertContains(self.client.get(response.url.split("#")[0]), f'id="answer-{answer.pk}"')

    def test_votes_and_permissions(self):
        answer = Answer.objects.create(question=self.question, author=self.reader, text="Ответ")
        for name, pk in [("question_vote", self.question.pk), ("answer_vote", answer.pk)]:
            url = reverse(name, args=[pk])
            self.client.logout()
            self.assertEqual(self.client.post(url, {"value": 1}).status_code, 401)
            self.client.force_login(self.reader)
            self.assertEqual(self.client.get(url).status_code, 405)
            self.assertEqual(self.client.post(url, {"value": 0}).status_code, 400)
            self.assertEqual(self.client.post(url, {"value": 1}).json()["rating"], 1)
            self.assertEqual(self.client.post(url, {"value": 1}).status_code, 409)
            self.assertEqual(self.client.post(url, {"value": -1}).json()["rating"], -1)
        url = reverse("correct_answer", args=[self.question.pk])
        self.assertEqual(self.client.post(url, {"answer": answer.pk}).status_code, 403)
        self.client.force_login(self.author)
        former = Answer.objects.create(question=self.question, author=self.reader, text="Первый", is_correct=True)
        self.assertTrue(self.client.post(url, {"answer": answer.pk}).json()["is_correct"])
        former.refresh_from_db()
        self.assertFalse(former.is_correct)
        self.assertFalse(self.client.post(url, {"answer": answer.pk}).json()["is_correct"])
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.author)
        response = csrf_client.post(url, {"answer": answer.pk})
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())
