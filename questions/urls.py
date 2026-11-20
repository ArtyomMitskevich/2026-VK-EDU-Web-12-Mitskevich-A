from django.urls import path
from . import views
from .models import Question, Answer

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot, name='hot'),
    path('tag/<slug:tag_slug>/', views.tag, name='tag'),
    path('question/<int:question_id>/', views.question, name='question'),
    path('ask/', views.ask, name='ask'),
    path('ajax/question/<int:object_id>/vote/', views.like_async, {'model': Question}, name='question_vote'),
    path('ajax/answer/<int:object_id>/vote/', views.like_async, {'model': Answer}, name='answer_vote'),
    path('ajax/question/<int:question_id>/correct/', views.correct_async, name='correct_answer'),
]
