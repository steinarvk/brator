import logging

from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

from ..logic import get_or_create_current_challenge
from ..logic import respond_to_challenge
from ..forms import CHALLENGE_FORMS
from ..exceptions import AlreadyResponded

logger = logging.getLogger(__name__)

@login_required
def index(request):
    challenge = get_or_create_current_challenge(request.user)
    formclass = CHALLENGE_FORMS[challenge.challenge_type]

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
        "form": form,
        "challenge": challenge,
    })

