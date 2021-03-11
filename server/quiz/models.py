from django.db import models
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.conf import settings

import inspect

from typing import List, Any

def TagField(choiceclass: models.TextChoices):
    return models.TextField(max_length=32, choices=choiceclass.choices)

def ConfidenceField():
    return models.DecimalField(max_digits=4, decimal_places=2)

def NumericField():
    return models.DecimalField(max_digits=32, decimal_places=2)

def _validate_tagged_union(obj, tag_field, suffix):
    class_name = obj.__class__.__name__

    tag = getattr(obj, tag_field)
    expected_field = tag + suffix

    if not getattr(obj, expected_field, None):
        raise ValidationError(f"{class_name}: {tag_field} is {tag}; {expected_field} must be set")

    field_names = [name for name in dir(obj) if name.endswith(suffix)]
    set_field_names = [name for name in field_names if getattr(obj, name, None)]

    if len(set_field_names) > 1:
        raise ValidationError(f"{class_name}: multiple tagged union fields set: {' '.join(set_field_names)}")

class FactType(models.TextChoices):
    BOOLEAN = "bool"
    NUMERIC = "numeric"

class Unit(models.TextChoices):
    NONE = "none"
    GRAMS_PER_CC = "g/cm³"

class BooleanFact(models.Model):
    question_text = models.TextField()
    correct_answer = models.BooleanField()

class NumericFact(models.Model):
    question_text = models.TextField()
    correct_answer_unit = models.CharField(max_length=32, choices = Unit.choices)
    correct_answer = NumericField()

class BooleanChallenge(models.Model):
    fact = models.ForeignKey(BooleanFact, on_delete=models.CASCADE)

class NumericChallenge(models.Model):
    fact = models.ForeignKey(NumericFact, on_delete=models.CASCADE)

class BooleanResponse(models.Model):
    challenge = models.ForeignKey(BooleanChallenge, on_delete=models.CASCADE)

class NumericResponse(models.Model):
    challenge = models.ForeignKey(NumericChallenge, on_delete=models.CASCADE)

    confidence_percent = ConfidenceField()
    ci_low = NumericField()
    ci_high = NumericField()

    def clean(self):
        if self.ci_low > self.ci_high:
            raise ValidationError(f"Confidence interval is reversed (low: {self.ci_low}, high: {self.ci_high}).")


class Fact(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)

    key = models.CharField(max_length = 200)
    active = models.BooleanField(default=True)

    fact_type = TagField(FactType)

    boolean_fact = models.ForeignKey(BooleanFact, on_delete=models.CASCADE, null=True, blank=True)
    numeric_fact = models.ForeignKey(NumericFact, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        _validate_tagged_union(self, "fact_type", "_fact")

class Challenge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(auto_now_add=True)

    fact = models.ForeignKey(Fact, on_delete=models.CASCADE)

    challenge_type = TagField(FactType)
    
    boolean_challenge = models.ForeignKey(BooleanChallenge, on_delete=models.CASCADE, null=True, blank=True)
    numeric_challenge = models.ForeignKey(NumericChallenge, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        _validate_tagged_union(self, "challenge_type", "_challenge")

class Response(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    challenge = models.OneToOneField(Challenge, on_delete=models.CASCADE)

    response_type = TagField(FactType)

    confidence_percent = ConfidenceField()
    correct = models.BooleanField()

    boolean_response = models.ForeignKey(BooleanResponse, on_delete=models.CASCADE, null=True, blank=True)
    numeric_response = models.ForeignKey(NumericResponse, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        _validate_tagged_union(self, "response_type", "_response")

def _register_models(maybe_models: List[Any]):
    for model in maybe_models:
        if not inspect.isclass(model):
            continue
        if not issubclass(model, models.Model):
            continue
        admin.site.register(model)

_register_models(globals().values())
