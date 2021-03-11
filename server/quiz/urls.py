from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register("facts", views.FactViewSet)
router.register("game", views.GameViewSet, basename="game")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]
