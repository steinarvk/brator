import logging

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

from ..logic import (
    get_or_create_current_challenge,
    respond_to_challenge,
    discard_current_challenge,
    get_last_response,
)
from ..forms import CHALLENGE_FORMS
from ..exceptions import AlreadyResponded

logger = logging.getLogger(__name__)

def index(request):
    return redirect(reverse("quiz:web-quiz"))

@login_required
def skip_question(request):
    if request.method == "POST":
        challenge_uid = request.POST.get("challenge_uid")
        discard_current_challenge(request.user, challenge_uid)

    return redirect(reverse("quiz:web-quiz"))

@login_required
def quiz(request):
    challenge = get_or_create_current_challenge(request.user)
    formclass = CHALLENGE_FORMS[challenge.challenge_type]

    last_response = get_last_response(request.user)

    logger.info("Form class is: %s", formclass)

    if request.method == "POST":
        form = formclass(request.POST)

        responding_to = request.POST["challenge_uid"]
        if responding_to != challenge.uid:
            raise AlreadyResponded()

        if form.is_valid():
            payload = {challenge.challenge_type: form.cleaned_data}

            feedback = respond_to_challenge(
                request.user,
                challenge.uid,
                payload,
            )

            return redirect(request.path_info)
    else:
        form = formclass()

    return render(request, "quiz/challenge.html", {
        "user": request.user,
        "last_response": last_response,
        "form": form,
        "challenge": challenge,
    })

