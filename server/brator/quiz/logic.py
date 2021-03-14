import secrets
import canonicaljson
import hashlib
import datetime
import logging
import random

import beeline

def traced_function(f):
    name = f.__name__
    return beeline.traced(name=name)(f)

from .models import (
    Fact,
    FactCategory,
    FactType,
    BooleanChallenge,
    NumericChallenge,
    Challenge,
    BooleanResponse,
    NumericResponse,
    Response,
    RESPONSE_MODELS,
    FACT_MODELS,
)

from .exceptions import (
    BadRequest,
    AlreadyResponded,
    NoFactsAvailable,
)

logger = logging.getLogger(__name__)

@traced_function
def generate_uid():
    return secrets.token_hex(16)

@traced_function
def select_random_fact():
    cats = [cat for cat in FactCategory.objects.all() if cat.active]
    logger.info(
        "Selecting random facts: categories: %s",
        [(cat.name, float(cat.weight)) for cat in cats],
    )
    cat_name = None
    if not cats:
        qs = Fact.objects.filter(active=True)
        logger.info("No categories -- using legacy random selection.")
    else:
        total_weight = float(sum(cat.weight for cat in cats))
        x = random.random() * total_weight
        for cat in cats:
            x -= float(cat.weight)
            if x < 0:
                break
        cat_name = cat.name
        qs = Fact.objects.filter(active=True, category=cat)
    logger.info("Choosing randomly (from category %s) among %d options", cat_name, qs.count())
    return qs.order_by("?").first()

@traced_function
def _save_and_return(x):
    x.save()
    return x

@traced_function
def create_boolean_challenge(fact):
    return _save_and_return(BooleanChallenge(fact=fact))

@traced_function
def create_numeric_challenge(fact):
    return _save_and_return(NumericChallenge(fact=fact))

@traced_function
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

@traced_function
def get_or_create_current_challenge(user):
    challenge = Challenge.objects.filter(
        user = user,
        active = True,
        response__isnull = True,
    ).order_by("-creation_time").first()

    if not challenge:
        fact = select_random_fact()
        if not fact:
            raise NoFactsAvailable()
        challenge = create_challenge_from_fact(user, fact)

    return challenge

@traced_function
def discard_current_challenge(user, challenge_uid=None):
    qs = Challenge.objects.filter(
        user = user,
        active = True,
        response__isnull = True,
    )
    if challenge_uid:
        qs = qs.filter(uid = challenge_uid)
    return qs.update(active = False)

@traced_function
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

    response_cls = RESPONSE_MODELS[k]

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

@traced_function
def get_last_response(user):
    return Response.objects.filter(
        user = user,
    ).order_by("-creation_time").first()

@traced_function
def get_user_responses(user, limit):
    return Response.objects.filter(
        user = user,
    ).order_by("creation_time").reverse()[:limit]

@traced_function
def post_fact(fact_data):
    fact_data = dict(fact_data)

    key = fact_data.pop("key")

    category_name = None
    if "category" in fact_data:
        category_name = fact_data.pop("category")

    category = None
    if category_name:
        category, _ = FactCategory.objects.get_or_create(name = category_name)

    logger.info("Attempting to post new fact (with key: %s)", key)

    if len(fact_data) != 1:
        raise BadRequest(f"Invalid fact data (unknown type): {' '.join(fact_data)}")

    fact_type = list(fact_data)[0]
    fact_payload = list(fact_data.values())[0]
    fact_hashable_obj = {
        "category": category_name,
        fact_type: fact_payload,
    }
    fact_hashable = canonicaljson.encode_canonical_json(fact_hashable_obj)

    fact_hash = hashlib.sha256(fact_hashable).hexdigest()

    logger.info("Attempting to post new fact (with key: %s, hash: %s)", key, fact_hash)

    old_fact = Fact.objects.filter(
        key = key,
        active = True,
    ).first()
    if old_fact:
        if old_fact.version_hash and old_fact.version_hash == fact_hash:
            logger.info("Attempting to post new fact (with key: %s, hash: %s): rejected, same as active fact", key, fact_hash)
            return old_fact

    field_name = fact_type + "_fact"

    core = FACT_MODELS[fact_type].objects.create(**fact_payload)

    Fact.objects.filter(key = key).update(active = False)
    return Fact.objects.create(
        key = key,
        active = True,
        category = category,
        version_hash = fact_hash,
        fact_type = fact_type,
        **{field_name: core},
    )


def get_eval_stats_for_scope(user, **kwargs):
    qs = Response.objects.filter(user=user, **kwargs)
    objs = list(qs.all())
    correct = [o for o in objs if o.correct]
    expected = sum([o.confidence_percent/100 for o in objs])
    return {
        "number_of_answers": len(objs),
        "number_of_correct_answers": len(correct),
        "expected_correct_answers": expected,
    }

def get_eval_stats(user):
    now = datetime.datetime.now()
    cutoff_24h = now - datetime.timedelta(hours=24)
    rv = {
        "stats": {
            "total": get_eval_stats_for_scope(user),
            "24h": get_eval_stats_for_scope(user, creation_time__gte=cutoff_24h),
        },
    }
    logger.info("Returning evaluation stats: %s", repr(rv))
    return rv

