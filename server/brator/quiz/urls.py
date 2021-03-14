from django.urls import path, include
from rest_framework import routers

from .views import api, web, web_urls

router = routers.DefaultRouter()
router.register("facts", api.FactViewSet, basename="facts")
router.register("quiz", api.GameViewSet, basename="quiz")
router.register("eval", api.EvalViewSet, basename="eval")

app_name = "quiz"
urlpatterns = [
    path("api/", include(router.urls), name="api"),
    path("", include(web_urls)),
]
