from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import reverse
from .data import QUESTIONS
from .pagination import paginate


@override_settings(ALLOWED_HOSTS=['testserver'])
class PageTests(SimpleTestCase):
    def test_main_routes(self):
        for name in ['index', 'hot', 'ask', 'login', 'signup', 'profile']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_unique_questions_and_page_boundaries(self):
        self.assertEqual(len(QUESTIONS), 15)
        self.assertEqual(len({q['id'] for q in QUESTIONS}), 15)
        first = self.client.get(reverse('index'))
        last = self.client.get(reverse('index'), {'page': 4})
        self.assertEqual(len(first.context['questions']), 4)
        self.assertEqual(len(last.context['questions']), 3)
        self.assertFalse(last.context['page_obj'].has_next())

    def test_invalid_page_parameters(self):
        factory = RequestFactory()
        for value in ['abc', '0', '-1', '9999', '1.5', '']:
            with self.subTest(value=value):
                page = paginate(QUESTIONS, factory.get('/', {'page': value}), 4)
                self.assertEqual(page.number, 1)

    def test_empty_list(self):
        page = paginate([], RequestFactory().get('/'), 4)
        self.assertEqual(list(page), [])
        self.assertEqual(page.number, 1)

    def test_hot_sorted_before_pagination(self):
        response = self.client.get(reverse('hot'))
        expected = sorted(QUESTIONS, key=lambda q: q['rating'], reverse=True)[:4]
        self.assertEqual(response.context['questions'], expected)

    def test_tag_filter_and_empty_tag(self):
        response = self.client.get(reverse('tag', args=['electronics']))
        self.assertTrue(all(any(t['slug'] == 'electronics' for t in q['tags']) for q in response.context['questions']))
        empty = self.client.get(reverse('tag', args=['cad']))
        self.assertEqual(empty.context['questions'], [])

    def test_unknown_objects(self):
        self.assertEqual(self.client.get(reverse('question', args=[999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('tag', args=['unknown'])).status_code, 404)

    def test_question_and_answer_pagination(self):
        for item in QUESTIONS:
            response = self.client.get(reverse('question', args=[item['id']]))
            self.assertEqual(response.context['question']['id'], item['id'])
        second = self.client.get(reverse('question', args=[35]), {'page': 2})
        self.assertEqual(len(second.context['answers']), 1)
        self.assertEqual(second.context['page_obj'].number, 2)
