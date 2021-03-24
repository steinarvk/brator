from django.urls import path, include
from rest_framework import routers

from .views import api, web, web_urls

router = routers.DefaultRouter()
router.register("quiz", api.GameViewSet, basename="quiz")
router.register("eval", api.EvalViewSet, basename="eval")

app_name = "quiz"
urlpatterns = [
    path("api/facts/export/", api.export_facts_view, name="api-facts-export"),
    path("api/facts/import/", api.import_facts_view, name="api-facts-import"),
    path("api/categories/export/", api.export_fact_categories_view, name="api-categories-export"),
    path("api/categories/import/", api.import_fact_categories_view, name="api-categories-import"),
    path("api/", include(router.urls), name="api"),
    path("", include(web_urls)),
]
