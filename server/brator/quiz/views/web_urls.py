from django.urls import path, include

from . import web

urlpatterns = [
    path("quiz/", web.quiz, name="web-quiz"),
    path("quiz/skip/", web.skip_question, name="web-skip"),
    path("eval/", web.eval_results, name="web-eval"),
    path("feedback/", web.feedback, name="web-feedback"),
    path("account/", web.account_settings, name="web-account"),
    path("account/delete/", web.delete_account, name="web-deleteaccount"),
    path("", web.index, name="web-index"),
]
