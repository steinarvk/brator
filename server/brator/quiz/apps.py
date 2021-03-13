from django.apps import AppConfig
from django.conf import settings

import beeline

class QuizConfig(AppConfig):
    name = 'brator.quiz'

    def ready(self):
        import brator.quiz.signals  # Imported for side-effects

        if settings.HONEYCOMB_API_KEY:
            beeline.init(
                writekey = settings.HONEYCOMB_API_KEY,
                dataset = settings.HONEYCOMB_DATASET,
                service_name = settings.HONEYCOMB_SERVICE,
            )
