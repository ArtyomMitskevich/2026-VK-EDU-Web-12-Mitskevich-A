from random import Random
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from core.models import Profile
from questions.models import Answer, AnswerLike, Question, QuestionLike, Tag, VoteValue


class Command(BaseCommand):
    help = "Добавляет в базу тестовых пользователей, вопросы, теги, ответы и оценки."
    batch_size = 2000

    def add_arguments(self, parser):
        parser.add_argument("ratio", type=int, nargs="?", default=10000)

    @transaction.atomic
    def handle(self, *args, **options):
        ratio = options["ratio"]
        # У одного пользователя на 10 вопросов и 100 ответов максимум 110 голосов.
        if ratio < 2:
            raise CommandError("Нужен ratio от 2, чтобы создать все оценки без повторных голосов.")

        fake = Faker("ru_RU")
        rng = Random()
        run = uuid4().hex[:12]
        User = get_user_model()
        users = User.objects.bulk_create([
            User(
                username=f"demo_{run}_{i}",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=f"demo_{run}_{i}@example.invalid",
                password=make_password(None),
            )
            for i in range(ratio)
        ], batch_size=self.batch_size)
        Profile.objects.bulk_create(
            [Profile(user_id=user.pk) for user in users], batch_size=self.batch_size,
        )
        tags = Tag.objects.bulk_create([
            Tag(name=f"{fake.word()} {run}-{i}", slug=f"demo-{run}-{i}")
            for i in range(ratio)
        ], batch_size=self.batch_size)

        # Готовим пул фраз заранее. При большом ratio стоимость Faker не растёт
        # пропорционально миллиону ответов, но сочетания текстов остаются разными.
        titles = [fake.sentence(nb_words=6) for _ in range(1000)]
        paragraphs = [fake.paragraph(nb_sentences=3) for _ in range(2000)]
        for start in range(0, ratio * 10, 500):
            count = min(500, ratio * 10 - start)
            self.create_batch(count, users, tags, titles, paragraphs, rng)

        self.stdout.write(self.style.SUCCESS(
            f"Добавлено: пользователей и профилей — по {ratio}, тегов — {ratio}, "
            f"вопросов — {ratio * 10}, ответов — {ratio * 100}, оценок — {ratio * 200}."
        ))

    def create_batch(self, count, users, tags, titles, paragraphs, rng):
        questions = Question.objects.bulk_create([
            Question(author_id=rng.choice(users).pk, title=rng.choice(titles)[:200],
                     text=rng.choice(paragraphs))
            for _ in range(count)
        ], batch_size=self.batch_size)
        link = Question.tags.through
        link.objects.bulk_create([
            link(question_id=question.pk, tag_id=tag.pk)
            for question in questions
            for tag in rng.sample(tags, k=min(3, len(tags)))
        ], batch_size=self.batch_size)
        answers = Answer.objects.bulk_create([
            Answer(question_id=question.pk, author_id=rng.choice(users).pk,
                   text=rng.choice(paragraphs), is_correct=position == 0)
            for question in questions
            for position in range(10)
        ], batch_size=self.batch_size)

        values = VoteValue.values
        QuestionLike.objects.bulk_create([
            QuestionLike(question_id=question.pk, user_id=rng.choice(users).pk,
                         value=rng.choice(values))
            for question in questions
        ], batch_size=self.batch_size)
        # Один голос за вопрос плюс 19 за его 10 ответов. Для каждого ответа
        # выбираем разных пользователей, поэтому уникальность не нарушается.
        AnswerLike.objects.bulk_create([
            AnswerLike(answer_id=answer.pk, user_id=user.pk, value=rng.choice(values))
            for index, answer in enumerate(answers)
            for user in rng.sample(users, k=1 if index % 10 == 0 else 2)
        ], batch_size=self.batch_size)
