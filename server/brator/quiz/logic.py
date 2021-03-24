import secrets
import canonicaljson
import hashlib
import decimal
import datetime
import logging
import random

from . import apitype

import beeline

STANDARD_SUMMARY_BATCHES = [20, 50]

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
    SummaryScore,
    RESPONSE_MODELS,
    FACT_MODELS,
)

from .stats import (
    calculate_plausibility_of,
)

from .exceptions import (
    BadRequest,
    AlreadyResponded,
    NoFactsAvailable,
    PermissionDenied,
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

    rv = _save_and_return(Response(
        user = user,
        challenge = challenge,
        confidence_percent = confidence,
        correct = is_correct,
        response_type = k,
        **{response_field: response_core},
    ))

    for batch_size in STANDARD_SUMMARY_BATCHES:
        maybe_summarize_responses(user, batch_size)

    return rv

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

def _maybe_pop(d, k):
    if k in d:
        return d.pop(k)
    return None

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

    kwargs = {
        "category": category_name,
        "source_link": _maybe_pop(fact_data, "source_link"),
        "source": _maybe_pop(fact_data, "source"),
        "fine_print": _maybe_pop(fact_data, "fine_print"),
    }

    if len(fact_data) != 1:
        raise BadRequest(f"Invalid fact data (unknown type): {' '.join(fact_data)}")

    fact_type = list(fact_data)[0]
    fact_payload = list(fact_data.values())[0]
    fact_hashable_obj = {
        fact_type: fact_payload,
        **kwargs,
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

    kwargs["category"] = category
    kwargs[field_name] = core

    Fact.objects.filter(key = key).update(active = False)
    return Fact.objects.create(
        key = key,
        active = True,
        version_hash = fact_hash,
        fact_type = fact_type,
        **kwargs,
    )

@traced_function
def get_eval_stats_for_scope(user, limit=None, **kwargs):
    qs = Response.objects.filter(user=user, **kwargs)
    if limit is None:
        objs = list(qs.all())
    else:
        objs = qs.order_by("-creation_time")[:limit]
    correct = [o.correct for o in objs]
    confidences = [o.confidence_percent/100 for o in objs]
    assert len(correct) == len(confidences)
    expected = sum(confidences)
    confidence_correctness = list(zip(confidences, correct))
    plausibility = calculate_plausibility_of(confidence_correctness)
    return {
        "number_of_answers": len(objs),
        "number_of_correct_answers": sum(correct),
        "expected_correct_answers": expected,
        "plausibility": plausibility,
    }

@traced_function
def get_eval_stats(user):
    now = datetime.datetime.now()
    cutoff_24h = now - datetime.timedelta(hours=24)
    rv = {
        "stats": {
            "total": get_eval_stats_for_scope(user),
            "24h": get_eval_stats_for_scope(user, creation_time__gte=cutoff_24h),
            "last50": get_eval_stats_for_scope(user, limit=50),
            "last10": get_eval_stats_for_scope(user, limit=10),
        },
    }
    logger.info("Returning evaluation stats: %s", repr(rv))
    return rv

@traced_function
def get_summarizable_responses_qs(user, batch_size):
    return Response.objects.filter(
        user = user,
        resolved = True,
    ).exclude(
        summary_scores__batch_size = batch_size,
    ).order_by("creation_time")

@traced_function
def get_summarizable_responses(user, batch_size):
    qs = get_summarizable_responses_qs(user, batch_size)
    if qs.count() < batch_size:
        return None
    return qs[:batch_size]

@traced_function
def maybe_summarize_responses(user, batch_size):
    batch = get_summarizable_responses(user, batch_size)
    if not batch:
        return None

    conf_corr = [
        (float(x.confidence_percent/100), x.correct)
        for x in batch
    ]

    actual_correct = sum(corr for _, corr in conf_corr)
    expected_correct = sum(float(conf) for conf, _ in conf_corr)

    resp = calculate_plausibility_of(conf_corr)
    assert resp

    rv = SummaryScore.objects.create(
        user = user,
        batch_size = batch_size,
        actual_correct = actual_correct,
        expected_correct = expected_correct,
        probability_fewer_correct = resp["prob_fewer"],
        probability_same_correct = resp["prob_same"],
        probability_more_correct = resp["prob_more"],
    )
    rv.datapoints.set(batch)
    return rv

@traced_function
def get_last_summary(user, batch_size=None):
    batch_size = batch_size or STANDARD_SUMMARY_BATCHES[0]
    return SummaryScore.objects.filter(
        user = user,
        batch_size = batch_size,
    ).order_by("-creation_time").first()

@traced_function
def get_batch_progress(user, batch_size=None):
    batch_size = batch_size or STANDARD_SUMMARY_BATCHES[0]
    qs = get_summarizable_responses_qs(user, batch_size)
    achieved = min(batch_size, qs.count())
    return achieved, batch_size

@traced_function
def get_largest_standard_summarized_batch_size(user):
    active_batch_sizes = SummaryScore.objects.filter(
        user = user,
    ).values_list("batch_size", flat=True).distinct()
    logger.info("Active batch sizes: %s", repr(active_batch_sizes))

    active_std = set(active_batch_sizes) & set(STANDARD_SUMMARY_BATCHES)

    logger.info("Active standard batch sizes (%s): %s", repr(STANDARD_SUMMARY_BATCHES), repr(active_std))
    if not active_std:
        return None

    return max(active_std)

@traced_function
def get_challenge_by_uid(user, uid):
    return Challenge.objects.get(user = user, uid = uid)

@traced_function
def delete_user_account(user):
    user.delete()

@traced_function
def get_summary_chart_data(user, batch_size = None):
    batch_size = batch_size or get_largest_standard_summarized_batch_size(user)

    if not batch_size:
        return None

    timestamps = []
    lower = []
    upper = []

    scores = SummaryScore.objects.filter(
        user = user,
        batch_size = batch_size,
    ).all()

    if not scores:
        return None

    for score in scores:
        timestamps.append(score.creation_time.strftime("%Y-%m-%d %H:%M"))

    return {
	"type": "line",
	"data": {
                "labels": [str(x) for x in timestamps],
		"datasets": [
                    {
                        "label": "Fewer (underconfident)",
			"data": [x.probability_fewer_correct for x in scores],
                        "borderColor": "#ffaaaa",
                        "backgroundColor": "#ee9999",
                    },
                    {
                        "label": "Same (calibrated)",
			"data": [x.probability_same_correct for x in scores],
                        "borderColor": "#aaffaa",
                        "backgroundColor": "#99ee99",
                    },
                    {
                        "label": "More (overconfident)",
			"data": [x.probability_more_correct for x in scores],
                        "borderColor": "#aaaaff",
                        "backgroundColor": "#9999ee",
                    },
                ],
	},
        "options": {
            "title": {
                "display": True,
                "text": f"Expected correct answers given calibration (batches of {batch_size})",
            },
            "tooltips": {
                "mode": "index",
            },
            "scales": {
                "yAxes": [
                    {
                        "stacked": True,
                    },
                ],
            },
        },
    }

@traced_function
def export_facts(user):
    if not user.is_staff:
        logger.info("User (%s) is not staff user: refusing export", repr(user))
        raise PermissionDenied()

    qs = Fact.objects.filter(
        active = True,
    ).select_related("category")

    logger.info("Exporting %d facts.", qs.count())

    rv = []

    for obj in qs.order_by("pk"):
        attrname = obj.fact_type + "_fact"
        kwargs = getattr(obj, attrname).export()

        logger.info("Exporting fact: %s (cat: %s)", repr(obj), repr(obj.category))

        rv.append(apitype.Fact(
            key = obj.key,
            category = obj.category.name if obj.category else None,
            fine_print = obj.fine_print,
            source = obj.source,
            source_link = obj.source_link,
            **kwargs,
        ))

    return [{k: v for k, v in x.dict().items() if v} for x in rv]

@traced_function
def export_fact_categories(user):
    if not user.is_staff:
        logger.info("User (%s) is not staff user: refusing export", repr(user))
        raise PermissionDenied()

    qs = FactCategory.objects.all()

    logger.info("Exporting %d fact categories.", qs.count())

    rv = []

    for obj in qs.order_by("pk"):
        rv.append(apitype.FactCategory(
            name = obj.name,
            weight = decimal.Decimal(obj.weight),
        ))

    return [{k: v for k, v in x.dict().items() if v} for x in rv]

@traced_function
def post_fact_category(cat_data):
    cat = apitype.FactCategory.parse_obj(cat_data)

    old_cat = FactCategory.objects.filter(
        name = cat.name,
    ).first()

    if old_cat:
        old_cat.weight = cat.weight
        old_cat.save()
        return

    return FactCategory.objects.create(
        name = cat.name,
        weight = cat.weight,
    )
