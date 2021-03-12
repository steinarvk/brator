from django.apps import AppConfig

class QuizConfig(AppConfig):
    name = 'brator.quiz'

    def ready(self):
        import brator.quiz.signals
