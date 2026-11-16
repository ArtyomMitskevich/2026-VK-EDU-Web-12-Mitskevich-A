from django.contrib import admin

from .models import Answer, AnswerLike, Question, QuestionLike, Tag


class AnswerInline(admin.TabularInline):
    """Ответы можно добавить и отредактировать прямо в карточке вопроса."""

    model = Answer
    fields = ("author", "text", "is_correct", "created_at")
    readonly_fields = ("author", "created_at")
    extra = 0

    def get_queryset(self, request):
        # Подписи авторов для всех ответов загружаются одним запросом.
        return super().get_queryset(request).select_related("author")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "text", "author__username")
    list_filter = ("created_at",)
    list_select_related = ("author",)
    # Поиск по мере ввода вместо выпадающих списков со всеми авторами и тегами.
    autocomplete_fields = ("author", "tags")
    inlines = (AnswerInline,)

    def save_formset(self, request, form, formset, change):
        # Ответ, добавленный прямо в карточке, принадлежит текущему администратору.
        answers = formset.save(commit=False)
        for answer in formset.deleted_objects:
            answer.delete()
        for answer in answers:
            if answer._state.adding:
                answer.author = request.user
            answer.save()
        formset.save_m2m()


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "author", "is_correct", "created_at")
    search_fields = ("text", "question__title", "author__username")
    list_filter = ("is_correct", "created_at")
    list_select_related = ("question", "author")
    autocomplete_fields = ("question", "author")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    list_filter = (("questions", admin.EmptyFieldListFilter),)
    prepopulated_fields = {"slug": ("name",)}


# Связанные объекты загружаются вместе с оценками для всей страницы списка.
@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "value")
    search_fields = ("user__username", "question__title")
    list_filter = ("value",)
    list_select_related = ("user", "question")
    autocomplete_fields = ("user", "question")


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "answer", "value")
    search_fields = ("user__username", "answer__text")
    list_filter = ("value",)
    list_select_related = ("user", "answer")
    autocomplete_fields = ("user", "answer")
