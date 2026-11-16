"""Общая пагинация для списков вопросов и ответов."""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


def paginate(objects_list, request, per_page=10):
    """Возвращает страницу; неправильный номер заменяет на первую страницу."""
    paginator = Paginator(objects_list, per_page)
    number = request.GET.get("page", 1)
    try:
        page = paginator.page(number)
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)
    # На большой базе показываем края списка и соседей текущей страницы.
    page.visible_numbers = list(paginator.get_elided_page_range(page.number))
    return page
