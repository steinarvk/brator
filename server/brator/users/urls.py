from django.conf.urls import include, url
from . import views

app_name = "users"
urlpatterns = [
    url(r"^accounts/", include("django.contrib.auth.urls")),
    url(r"^register/", views.register, name="register"),
]
