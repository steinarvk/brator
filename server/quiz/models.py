from django.db import models
from django.contrib import admin
from django.core.exceptions import ValidationError

class FactType(models.TextChoices):
    BOOLEAN = "bool"
    NUMERIC = "numeric"

class Unit(models.TextChoices):
    NONE = "none"
    GRAMS_PER_CC = "g/cm³"

class BooleanFact(models.Model):
    question_text = models.TextField()
    correct_answer = models.BooleanField()
admin.site.register(BooleanFact)

class NumericFact(models.Model):
    question_text = models.TextField()
    correct_answer_unit = models.CharField(max_length=32, choices = Unit.choices)
    correct_answer = models.DecimalField(max_digits=32, decimal_places=2)
admin.site.register(NumericFact)

class Fact(models.Model):
    creation_time = models.DateTimeField(auto_now_add=True)

    key = models.CharField(max_length = 200)
    active = models.BooleanField(default=True)

    fact_type = models.CharField(
        max_length = 32,
        choices = FactType.choices)

    boolean_fact = models.ForeignKey(BooleanFact, on_delete=models.CASCADE, null=True, blank=True)
    numeric_fact = models.ForeignKey(NumericFact, on_delete=models.CASCADE, null=True, blank=True)

    def clean(self):
        expected_attr = self.fact_type + "_fact"
        value = getattr(self, expected_attr, None)
        if not value:
            raise ValidationError(f"Fact has type {self.fact_type} but field {expected_attr} is not set")

        fact_fields = [name for name in dir(self) if name.endswith("_fact")]
        set_fact_fields = [name for name in fact_fields if getattr(self, name, None)]
        if len(set_fact_fields) > 1:
            raise ValidationError(f"Fact has multiple payloads: {' '.join(set_fact_fields)}")
admin.site.register(Fact)
