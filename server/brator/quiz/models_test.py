import pytest

from .models import Fact, BooleanFact, NumericFact

from django.test import TestCase


class ModelTest(TestCase):

    def test_create_ok_model(self):
        Fact.objects.create(
            key = "foo",
            fact_type = "boolean",
            boolean_fact = BooleanFact.objects.create(
                question_text = "Yes?",
                correct_answer = True,
            ),
        )

    def test_create_broken_model(self):
        with pytest.raises(Exception):
            Fact.objects.create(
                key = "foo",
                fact_type = "numeric",
                boolean_fact = BooleanFact.objects.create(
                    question_text = "Yes?",
                    correct_answer = True,
                ),
            )

    def test_create_another_broken_model(self):
        with pytest.raises(Exception):
            Fact.objects.create(
                key = "foo",
                fact_type = "numeric",
            )

    def test_create_broken_model_3(self):
        with pytest.raises(Exception):
            Fact.objects.create(
                key = "foo",
                fact_type = "numeric",
                boolean_fact = BooleanFact.objects.create(
                    question_text = "Yes?",
                    correct_answer = True,
                ),
                numeric_fact = NumericFact.objects.create(
                    question_text = "?",
                    correct_answer = 42,
                    correct_answer_unit = "none",
                ),
            )

    def test_create_broken_model_4(self):
        with pytest.raises(Exception):
            Fact.objects.create(
                key = "foo",
            )

    def test_create_broken_model_5(self):
        with pytest.raises(Exception):
            Fact.objects.create(
                fact_type = "boolean",
                boolean_fact = BooleanFact.objects.create(
                    question_text = "Yes?",
                    correct_answer = True,
                ),
            )

    def test_create_another_ok_model(self):
        Fact.objects.create(
            key = "foo",
            fact_type = "numeric",
            numeric_fact = NumericFact.objects.create(
                question_text = "?",
                correct_answer = 42,
                correct_answer_unit = "none",
            ),
        )

    def test_create_broken_model_6(self):
        with pytest.raises(Exception):
            Fact.objects.create(
                key = "foo",
                fact_type = "numeric",
                numeric_fact = NumericFact.objects.create(
                    question_text = "?",
                    correct_answer = 42,
                ),
            )
