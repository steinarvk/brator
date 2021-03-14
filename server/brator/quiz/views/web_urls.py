from django.urls import path, include

from . import web

urlpatterns = [
    path("quiz/", web.quiz, name="web-quiz"),
    path("quiz/skip/", web.skip_question, name="web-skip"),
    path("eval/", web.eval_results, name="web-eval"),
    path("", web.index, name="web-index"),
]
