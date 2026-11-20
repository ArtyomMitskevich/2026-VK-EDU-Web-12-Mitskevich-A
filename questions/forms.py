from uuid import uuid4

from django import forms
from django.db import transaction
from django.db.models import Sum
from django.utils.text import slugify

from .models import Answer, Question, Tag, VoteValue


class QuestionForm(forms.ModelForm):
    tag_names = forms.CharField(label="Теги", help_text="Введите теги через запятую.")

    class Meta:
        model = Question
        fields = ("title", "text")

    def clean_tag_names(self):
        names = [part.strip().lower() for part in self.cleaned_data["tag_names"].split(",")]
        if any(not name or len(name) > 50 for name in names):
            raise forms.ValidationError("Введите названия тегов длиной от 1 до 50 символов.")
        return list(dict.fromkeys(names))

    @transaction.atomic
    def save(self, user):
        question = super().save(commit=False)
        question.author = user
        question.save()
        for name in sorted(self.cleaned_data["tag_names"]):
            # Для кириллических тегов тоже нужен адрес, подходящий под slug-маршрут.
            slug = f"{slugify(name)[:25] or 'tag'}-{uuid4().hex}"
            tag, _ = Tag.objects.get_or_create(name=name, defaults={"slug": slug})
            question.tags.add(tag)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ("text",)
        labels = {"text": "Текст ответа"}

    def save(self, user, question):
        answer = super().save(commit=False)
        answer.author = user
        answer.question = question
        answer.save()
        return answer


class VoteForm(forms.Form):
    value = forms.TypedChoiceField(choices=VoteValue.choices, coerce=int)

    def save(self, target, user):
        # Вью блокирует строку вопроса или ответа на время смены голоса и подсчёта.
        value = self.cleaned_data["value"]
        vote, created = target.likes.get_or_create(user=user, defaults={"value": value})
        if not created:
            if vote.value == value:
                raise forms.ValidationError("Вы уже поставили эту оценку.")
            vote.value = value
            vote.save(update_fields=["value"])
        return target.likes.aggregate(total=Sum("value"))["total"]


class CorrectAnswerForm(forms.Form):
    answer = forms.ModelChoiceField(queryset=Answer.objects.none())

    def __init__(self, question, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.question = question
        self.fields["answer"].queryset = question.answers.all()

    def save(self):
        answer = self.cleaned_data["answer"]
        self.question.answers.filter(is_correct=True).exclude(pk=answer.pk).update(is_correct=False)
        answer.is_correct = not answer.is_correct
        answer.save(update_fields=["is_correct"])
        return answer
