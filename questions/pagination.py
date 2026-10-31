"""Общая пагинация для списков вопросов и ответов."""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    """Возвращает страницу; неправильный номер заменяет на первую страницу."""
    paginator = Paginator(objects_list, per_page)
    number = request.GET.get("page", 1)
    try:
        return paginator.page(number)
    except (PageNotAnInteger, EmptyPage):
        return paginator.page(1)
