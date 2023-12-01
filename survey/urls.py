from django.urls import path
from django.contrib.auth.decorators import login_required

from survey.views import (QuestionTemplateView,
                          QuestionCreateView,
                          QuestionUpdateView,
                          questions,
                          answer_question,
                          like_dislike_question)

urlpatterns = [
    path('', QuestionTemplateView.as_view(), name='question-list'),
    path('questions', questions, name='question-all'),
    path('question/add', login_required(QuestionCreateView.as_view()), name='question-create'),
    path('question/edit/<int:pk>', login_required(QuestionUpdateView.as_view()), name='question-edit'),
    path('question/new', login_required(QuestionCreateView.as_view()), name='question-new'),
    path('question/answer', answer_question, name='question-answer'),
    path('question/like', like_dislike_question, name='question-like'),
]