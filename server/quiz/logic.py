import secrets

from .models import (
    Fact,
    FactType,
    BooleanChallenge,
    NumericChallenge,
    Challenge,
    BooleanResponse,
    NumericResponse,
    Response,
)

from .exceptions import BadRequest, AlreadyResponded

def generate_uid():
    return secrets.token_hex(16)

def select_random_fact():
    return Fact.objects.\
        filter(active=True).\
        order_by("?").\
        first()

def _save_and_return(x):
    x.save()
    return x

def create_boolean_challenge(fact):
    return _save_and_return(BooleanChallenge(fact=fact))

def create_numeric_challenge(fact):
    return _save_and_return(NumericChallenge(fact=fact))

def create_challenge_from_fact(user, fact):
    creators = {
        "boolean_fact": create_boolean_challenge,
        "numeric_fact": create_numeric_challenge,
    }
    kw = {
        k.replace("_fact", "_challenge"): f(getattr(fact, k))
        for k, f in creators.items()
        if getattr(fact, k)
    }
    return _save_and_return(Challenge(
        uid = generate_uid(),
        user = user,
        fact = fact,
        challenge_type = fact.fact_type,
        **kw,
    ))

def get_or_create_current_challenge(user):
    challenge = Challenge.objects.filter(
        user = user,
        active = True,
        response__isnull = True,
    ).order_by("-creation_time").first()

    if not challenge:
        fact = select_random_fact()
        challenge = create_challenge_from_fact(user, fact)

    return challenge

def discard_current_challenge(user):
    return Challenge.objects.filter(
        user = user,
        active = True,
        response__isnull = True,
    ).update(active = False)

def respond_to_challenge(user, challenge_uid, response):
    challenge = Challenge.objects.get(user = user, uid = challenge_uid)

    try:
        challenge.response
        raise AlreadyResponded(detail = f"Challenge {challenge_uid} has already gotten a response")
    except Challenge.response.RelatedObjectDoesNotExist:
        pass

    k = challenge.challenge_type
    if list(response) != [k]:
        raise BadRequest(detail = f"Challenge is of type {k}; got response of other type ({list(response)})")

    response_models = {
        FactType.BOOLEAN: BooleanResponse,
        FactType.NUMERIC: NumericResponse,
    }

    response_cls = response_models[k]

    response_core = _save_and_return(response_cls(
        challenge = challenge.challenge,
        **response[k],
    ))
    response_field = k + "_response"

    confidence = response_core.confidence_percent

    is_correct = response_core.get_correctness()

    return _save_and_return(Response(
        user = user,
        challenge = challenge,
        confidence_percent = confidence,
        correct = is_correct,
        response_type = k,
        **{response_field: response_core},
    ))

def get_user_responses(user, limit):
    return Response.objects.filter(
        user = user,
    ).order_by("creation_time").reverse()[:limit]

