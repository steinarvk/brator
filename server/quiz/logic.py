import secrets

from .models import Fact, BooleanChallenge, NumericChallenge, Challenge

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

