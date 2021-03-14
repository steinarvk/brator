from django.db import models
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.conf import settings

import re
import inspect

from typing import List, Any

UID_LENGTH = 32

def UidField():
    return models.CharField(max_length=UID_LENGTH, unique=True)

def TagField(choiceclass: models.TextChoices):
    return models.TextField(max_length=32, choices=choiceclass.choices)

def ConfidenceField():
    return models.DecimalField(max_digits=4, decimal_places=2)

def NumericField():
    return models.DecimalField(max_digits=32, decimal_places=2)

def _validate_tagged_union(obj, choiceclass, tag_field, suffix):
    class_name = obj.__class__.__name__

    tag = getattr(obj, tag_field)

    valid = [x[0] for x in choiceclass.choices]
    if tag not in valid:
        raise ValidationError(f"{class_name}: {tag_field} has illegal value {tag}; legal values: {' '.join(valid)}")

    expected_field = tag + suffix

    if not getattr(obj, expected_field, None):
        raise ValidationError(f"{class_name}: {tag_field} is {tag}; {expected_field} must be set")

    field_names = [name for name in dir(obj) if name.endswith(suffix)]
    set_field_names = [name for name in field_names if getattr(obj, name, None)]

    if len(set_field_names) > 1:
        raise ValidationError(f"{class_name}: multiple tagged union fields set: {' '.join(set_field_names)}")

class FactType(models.TextChoices):
    BOOLEAN = "boolean"
    NUMERIC = "numeric"

class Unit(models.TextChoices):
    NONE = "none"
    GRAMS_PER_CC = "g/cm³"
    SQUARE_KM = "sq km"
    PERCENT = "percent"
    KELVIN = "kelvin"
    CELSIUS = "celsius"
    METERS = "meters"
    MINUTES = "minutes"
    SECONDS = "seconds"
    GRAMS = "grams"

class BooleanFact(models.Model):
    question_text = models.TextField()
    correct_answer = models.BooleanField()

class NumericFact(models.Model):
    question_text = models.TextField()
    correct_answer_unit = models.CharField(max_length=32, choices = Unit.choices)
    correct_answer = NumericField()

    def clean(self):
        valid = [x[0] for x in Unit.choices]
        if self.correct_answer_unit not in valid:
            raise ValidationError(f"Not a valid unit: {self.correct_answer_unit}.")

class BooleanChallenge(models.Model):
    fact = models.ForeignKey(BooleanFact, on_delete=models.CASCADE)

class NumericChallenge(models.Model):
    fact = models.ForeignKey(NumericFact, on_delete=models.CASCADE)

def _check_confidence(pct):
    if not (0 < pct < 100):
        raise ValidationError(f"Confidence value out of bounds or at forbidden extreme ({pct})")

class BooleanResponse(models.Model):
    challenge = models.ForeignKey(BooleanChallenge, on_delete=models.CASCADE)
    answer = models.BooleanField()
    confidence_percent = ConfidenceField()

    def get_correctness(self):
        return self.challenge.fact.correct_answer == self.answer

    def clean(self):
        _check_confidence(self.confidence_percent)
        if self.confidence_percent < 50:
            raise ValidationError(f"Confidence for boolean question should not be lower than 50%.")

class NumericResponse(models.Model):
    challenge = models.ForeignKey(NumericChallenge, on_delete=models.CASCADE)

    confidence_percent = ConfidenceField()
    ci_low = NumericField()
    ci_high = NumericField()

    def clean(self):
        _check_confidence(self.confidence_percent)

        if self.ci_low > self.ci_high:
            raise ValidationError(f"Confidence interval is reversed (low: {self.ci_low}, high: {self.ci_high}).")

    def get_correctness(self):
        x = self.challenge.fact.correct_answer
        return self.ci_low <= x <= self.ci_high


class FactCategory(models.Model):
    name = models.CharField(max_length = 64, unique=True)

    weight = models.DecimalField(max_digits=8, decimal_places=2, default=1)

    @property
    def number_of_active_facts(self):
        return self.fact_set.filter(active=True).count()

    @property
    def active(self):
        return self.number_of_active_facts > 0

    def __str__(self):
        return f"FactCategory(name={repr(self.name)}, weight={repr(self.weight)})"

    def clean(self):
        if not re.match(r"^[a-z-]+$", self.name):
            raise ValidationError(f"Invalid category name: {self.name}")


class Fact(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)

    key = models.CharField(max_length = 200)
    active = models.BooleanField(default=True)

    category = models.ForeignKey(FactCategory, on_delete=models.SET_NULL, null=True)

    fact_type = TagField(FactType)

    version_hash = models.CharField(max_length = 200, null=True)

    boolean_fact = models.ForeignKey(BooleanFact, on_delete=models.CASCADE, null=True, blank=True)
    numeric_fact = models.ForeignKey(NumericFact, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        _validate_tagged_union(self, FactType, "fact_type", "_fact")

        if not self.key:
            raise ValidationError("No key supplied.")

class Challenge(models.Model):
    uid = UidField()

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(auto_now_add=True)

    fact = models.ForeignKey(Fact, on_delete=models.CASCADE)

    active = models.BooleanField(default=True)
    challenge_type = TagField(FactType)
    
    boolean_challenge = models.ForeignKey(BooleanChallenge, on_delete=models.CASCADE, null=True, blank=True)
    numeric_challenge = models.ForeignKey(NumericChallenge, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        _validate_tagged_union(self, FactType, "challenge_type", "_challenge")

    @property
    def challenge(self):
        return (
               self.boolean_challenge
            or self.numeric_challenge
        )

class Response(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE)

    confidence_percent = ConfidenceField()
    correct = models.BooleanField()

    response_type = TagField(FactType)

    boolean_response = models.ForeignKey(BooleanResponse, on_delete=models.CASCADE, null=True, blank=True)
    numeric_response = models.ForeignKey(NumericResponse, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        _validate_tagged_union(self, FactType, "response_type", "_response")

def _register_models(maybe_models: List[Any]):
    for model in maybe_models:
        if not inspect.isclass(model):
            continue
        if not issubclass(model, models.Model):
            continue
        admin.site.register(model)

RESPONSE_MODELS = {
    FactType.BOOLEAN: BooleanResponse,
    FactType.NUMERIC: NumericResponse,
}

FACT_MODELS = {
    FactType.BOOLEAN: BooleanFact,
    FactType.NUMERIC: NumericFact,
}

_register_models(globals().values())
