import secrets

from django.contrib.auth.models import User
from .models import Fact, NumericFact, BooleanFact

DUMMY_NUMERIC_FACT = {
    "key": "human-legs",
    "category": "legs-question",
    "numeric": {
        "question_text": "How many legs does a human have?",
        "correct_answer": 2,
        "correct_answer_unit": "none",
    },
}

DUMMY_BOOLEAN_FACT = {
    "key": "isaac-18th",
    "category": "scientist-question",
    "boolean": {
        "question_text": "Did Isaac Newton live in the 18th century?",
        "correct_answer": True,
    },
}

DUMMY_FACT_DATA = [
    DUMMY_NUMERIC_FACT,
    DUMMY_BOOLEAN_FACT,
    {
        "key": "spider-legs",
        "category": "legs-question",
        "numeric": {
            "question_text": "How many legs does a spider have?",
            "correct_answer": 8,
            "correct_answer_unit": "none",
        },
    },
]

def create_superuser():
    return User.objects.create_superuser(
        username="test_superuser",
        password=secrets.token_hex(32),
        email="test_superuser@example.com",
    )

def create_regular_user(username="user"):
    return User.objects.create(
        username=username,
        password=secrets.token_hex(32),
        email=username + "@example.com",
    )

def create_numeric_fact():
    data = dict(DUMMY_NUMERIC_FACT)
    return Fact.objects.create(
        key = data["key"],
        fact_type = "numeric",
        numeric_fact = NumericFact.objects.create(
            **data["numeric"],
        ),
    )

def create_custom_numeric_fact(question, answer, unit="none"):
    return Fact.objects.create(
        key = "customfact",
        fact_type = "numeric",
        numeric_fact = NumericFact.objects.create(
            question_text = question,
            correct_answer = answer,
            correct_answer_unit = unit,
        ),
    )

def create_boolean_fact():
    data = dict(DUMMY_BOOLEAN_FACT)
    return Fact.objects.create(
        key = data["key"],
        fact_type = "boolean",
        boolean_fact = BooleanFact.objects.create(
            **data["boolean"],
        ),
    )

def create_fact():
    create_numeric_fact()
