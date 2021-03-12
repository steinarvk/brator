from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register("facts", views.FactViewSet, basename="facts")
router.register("quiz", views.GameViewSet, basename="quiz")
router.register("eval", views.EvalViewSet, basename="eval")

urlpatterns = [
    path("api/", include(router.urls)),
]
