import logging

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

from ..logic import (
    get_or_create_current_challenge,
    get_eval_stats,
    get_challenge_by_uid,
    respond_to_challenge,
    discard_current_challenge,
    get_last_response,
    get_last_summary,
    get_batch_progress,
    get_largest_standard_summarized_batch_size,
    delete_user_account,
)
from ..models import ChallengeFeedback
from ..forms import CHALLENGE_FORMS
from ..forms import ChallengeFeedbackForm, DeleteMyAccountForm
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

    batch_size = get_largest_standard_summarized_batch_size(request.user)
    last_summary = get_last_summary(request.user, batch_size)
    batch_progress, _ = get_batch_progress(request.user, batch_size)

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
        "last_summary": last_summary,
        "summary_progress": {
            "progress": batch_progress,
            "batch_size": batch_size,
        },
        "form": form,
        "challenge": challenge,
        "feedback_form": ChallengeFeedbackForm(initial={
            "challenge_uid": challenge.uid,
        }),
    })

@login_required
def question_feedback(request, uid):
    challenge = get_challenge_by_uid(request.user, uid)

    form = ChallengeFeedbackForm(request.POST or None)

    if form.is_valid():
        form_data = form.cleaned_data

        ChallengeFeedback.objects.create(
            user = request.user,
            challenge = challenge,
            category = form_data["category"],
            text = form_data["text"],
        )

        return redirect(reverse("quiz:web-quiz"))

    return render(request, "quiz/standalone_feedback_form.html", {
        "challenge": challenge,
        "feedback_form": form,
    })

@login_required
def answer_feedback(request, uid):
    challenge = get_challenge_by_uid(request.user, uid)

    form = ChallengeFeedbackForm(request.POST or None)

    if form.is_valid():
        form_data = form.cleaned_data

        ChallengeFeedback.objects.create(
            user = request.user,
            challenge = challenge,
            category = form_data["category"],
            text = form_data["text"],
        )

        return redirect(reverse("quiz:web-quiz"))

    return render(request, "quiz/standalone_feedback_form_with_answer.html", {
        "show_answer": True,
        "challenge": challenge,
        "feedback_form": form,
    })


@login_required
def eval_results(request):
    context = get_eval_stats(request.user)
    context["user"] = request.user
    return render(request, "quiz/eval.html", context)

@login_required
def account_settings(request):
    return render(request, "quiz/account.html", {})

@login_required
def delete_account(request):
    if request.method == "POST":
        form = DeleteMyAccountForm(request.POST)

        if form.is_valid():
            delete_user_account(request.user)
    else:
        form = DeleteMyAccountForm()

    return render(request, "quiz/deleteme.html", {
        "confirmation_message": DeleteMyAccountForm.desired_confirmation_message,
        "form": form,
    })
