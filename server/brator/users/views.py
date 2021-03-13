from django.shortcuts import redirect, render
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get("username")
            plaintext_password = form.cleaned_data.get("password1")

            user = auth.authenticate(username=username, password=plaintext_password)
            auth.login(request, user)

            return redirect("/")
    else:
        form = UserCreationForm()
    return render(request, "users/register.html", {
        "form": form,
    })


