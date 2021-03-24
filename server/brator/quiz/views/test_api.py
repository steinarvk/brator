import json
import pytest

from django.test import TestCase
from django.urls import reverse

from ..models import Fact

from ..testutils import (
    create_superuser,
    create_regular_user,
    create_fact,
    create_numeric_fact,
    create_boolean_fact,
    DUMMY_FACT_DATA,
)

class ViewChallengeTest(TestCase):
    def setUp(self):
        self.superuser = create_superuser()
        self.user = create_regular_user()

    def test_get_challenge(self):
        create_fact()
        self.client.force_login(self.superuser)
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        data = resp.json()
        assert resp.status_code == 200
        assert data["fact"]["key"] == "human-legs"
        assert data["uid"]

    def test_get_no_challenge(self):
        self.client.force_login(self.superuser)
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        assert resp.status_code == 500

    def test_not_logged_in(self):
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        assert resp.status_code == 403

    def test_get_challenge_again(self):
        create_fact()
        self.client.force_login(self.superuser)

        resp = self.client.get(reverse("quiz:quiz-challenge"))
        assert resp.status_code == 200
        data = resp.json()
        old_timestamp = data["creation_time"]
        old_uid = data["uid"]
        assert old_timestamp
        assert old_uid

        resp = self.client.get(reverse("quiz:quiz-challenge"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["creation_time"] == old_timestamp
        assert data["uid"] == old_uid

    def test_discard_and_get_new_challenge(self):
        create_fact()
        self.client.force_login(self.superuser)

        resp = self.client.get(reverse("quiz:quiz-challenge"))
        assert resp.status_code == 200
        data = resp.json()
        old_timestamp = data["creation_time"]
        old_uid = data["uid"]
        assert old_timestamp
        assert old_uid

        resp = self.client.delete(reverse("quiz:quiz-challenge"))
        assert 200 <= resp.status_code <= 299

        resp = self.client.get(reverse("quiz:quiz-challenge"))
        assert resp.status_code == 200
        data = resp.json()
        assert data["creation_time"] != old_timestamp
        assert data["uid"] != old_uid

class FactsListTest(TestCase):
    def setUp(self):
        self.superuser = create_superuser()
        self.client.force_login(self.superuser)

    def test_get_facts_0(self):
        assert len(self.client.get(reverse("quiz:api-facts-export")).json()) == 0

    def test_get_facts_1(self):
        create_numeric_fact()
        assert len(self.client.get(reverse("quiz:api-facts-export")).json()) == 1

    def test_get_facts_2(self):
        create_numeric_fact()
        create_boolean_fact()
        assert len(self.client.get(reverse("quiz:api-facts-export")).json()) == 2

    def test_post_fact(self):
        resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=DUMMY_FACT_DATA[0])
        assert 200 <= resp.status_code <= 399
        assert resp.json()

    def test_post_good_fact(self):
        factdata = {
            "key": "foo",
            "numeric": {
                "question_text": "Hmm?",
                "correct_answer": 42,
                "correct_answer_unit": "none",
            },
        }
        assert Fact.objects.count() == 0
        resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=factdata)
        assert 200 <= resp.status_code <= 299
        assert Fact.objects.count() == 1

    def test_post_good_fact_with_category(self):
        factdata = {
            "key": "foo",
            "category": "my-category",
            "numeric": {
                "question_text": "Hmm?",
                "correct_answer": 42,
                "correct_answer_unit": "none",
            },
        }
        assert Fact.objects.count() == 0
        resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=factdata)
        assert 200 <= resp.status_code <= 299
        assert Fact.objects.count() == 1


    def test_post_bad_fact(self):
        bad_fact = {
            "key": "foo",
            "catfact": "miaow",
        }
        with pytest.raises(Exception):
            resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=bad_fact)

    def test_post_doubly_bad_fact(self):
        bad_fact = {
            "key": "foo",
            "catfact": "miaow",
            "dogfact": "woof",
        }
        resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=bad_fact)
        assert 400 <= resp.status_code <= 499

    def test_post_fact_and_count(self):
        assert Fact.objects.count() == 0
        self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=DUMMY_FACT_DATA[0])
        assert Fact.objects.count() == 1

    def test_post_all_facts(self):
        for x in DUMMY_FACT_DATA:
            resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=x)
            assert 200 <= resp.status_code <= 399
            assert resp.json()

    def test_post_all_facts_at_once(self):
        resp = self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=DUMMY_FACT_DATA)
        assert 200 <= resp.status_code <= 399
        assert resp.json()

    def test_get_facts(self):
        resp = self.client.get(reverse("quiz:api-facts-export"))
        assert 200 == resp.status_code
        assert resp.json() == []

    def test_post_same_fact_twice(self):
        assert Fact.objects.count() == 0
        self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=DUMMY_FACT_DATA[0])
        assert Fact.objects.count() == 1
        self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=DUMMY_FACT_DATA[0])
        assert Fact.objects.count() == 1
        self.client.post(reverse("quiz:api-facts-import"), content_type="application/json", data=DUMMY_FACT_DATA[1])
        assert Fact.objects.count() == 2


class QuizResponseTest(TestCase):
    def setUp(self):
        self.user = create_regular_user()
        self.client.force_login(self.user)

    def test_post_numeric_response(self):
        create_numeric_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        resp = self.client.post(uri, content_type="application/json", data={
            "numeric": {
                "ci_low": 1,
                "ci_high": 4,
                "confidence_percent": 90,
            },
        })
        assert 200 == resp.status_code
        assert self.client.get(reverse("quiz:quiz-challenge")).json()["uid"] != uid

    def test_post_bad_numeric_response(self):
        create_numeric_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        with pytest.raises(Exception):
            self.client.post(uri, content_type="application/json", data={
                "numeric": {
                    "ci_high": 1,
                    "ci_low": 4,
                    "confidence_percent": 90,
                },
            })

    def test_post_numeric_response_bad_extreme_confidence(self):
        create_numeric_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        with pytest.raises(Exception):
            resp = self.client.post(uri, content_type="application/json", data={
                "numeric": {
                    "ci_low": 1,
                    "ci_high": 4,
                    "confidence_percent": 100,
                },
            })

    def test_post_boolean_response(self):
        create_boolean_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        resp = self.client.post(uri, content_type="application/json", data={
            "boolean": {
                "answer": True,
                "confidence_percent": 75,
            },
        })
        assert 200 == resp.status_code
        assert self.client.get(reverse("quiz:quiz-challenge")).json()["uid"] != uid

    def test_post_bad_boolean_response(self):
        create_boolean_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        with pytest.raises(Exception):
            resp = self.client.post(uri, content_type="application/json", data={
                "boolean": {
                    "answer": True,
                    "confidence_percent": 25,
                },
            })

    def test_post_inappropriate_response(self):
        create_boolean_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        resp = self.client.post(uri, content_type="application/json", data={
            "numeric": {
                "ci_low": 1,
                "ci_high": 4,
                "confidence_percent": 90,
            },
        })
        assert resp.status_code == 400

    def test_post_double_boolean_response(self):
        create_boolean_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        uid = resp.json()["uid"]
        uri = reverse("quiz:quiz-response", args=[uid])
        resp = self.client.post(uri, content_type="application/json", data={
            "boolean": {
                "answer": True,
                "confidence_percent": 75,
            },
        })
        assert 200 == resp.status_code
        assert self.client.get(reverse("quiz:quiz-challenge")).json()["uid"] != uid
        resp = self.client.post(uri, content_type="application/json", data={
            "boolean": {
                "answer": True,
                "confidence_percent": 75,
            },
        })
        assert resp.status_code == 409


class EvalTest(TestCase):
    def setUp(self):
        self.user = create_regular_user()
        self.client.force_login(self.user)

    def test_get_scores(self):
        resp = self.client.get(reverse("quiz:eval-scores"))
        assert 200 == resp.status_code
        assert resp.json() == []

    def test_post_and_get_score(self):
        create_boolean_fact()
        resp = self.client.get(reverse("quiz:quiz-challenge"))
        self.client.post(
            reverse("quiz:quiz-response", args=[resp.json()["uid"]]),
            content_type="application/json",
            data={"boolean": {"answer": True, "confidence_percent": 75}},
        )

        resp = self.client.get(reverse("quiz:eval-scores"))
        assert 200 == resp.status_code
        data = resp.json()

        assert len(data) == 1
        assert data[0]["correct"] == True
        assert data[0]["confidence_percent"] == "75.00"

class FactCategoriesListTest(TestCase):
    def setUp(self):
        self.superuser = create_superuser()
        self.client.force_login(self.superuser)

    def test_get_categories_0(self):
        assert len(self.client.get(reverse("quiz:api-categories-export")).json()) == 0

    def test_post_category(self):
        assert self.client.post(
            reverse("quiz:api-categories-import"),
            content_type="application/json",
            data={
                "name": "my-category",
                "weight": 3,
            },
        ).status_code == 200
        assert len(self.client.get(reverse("quiz:api-categories-export")).json()) == 1

    def test_post_category_twice(self):
        for i in range(2):
            assert self.client.post(
                reverse("quiz:api-categories-import"),
                content_type="application/json",
                data={
                    "name": "my-category",
                    "weight": 3,
                },
            ).status_code == 200
        assert len(self.client.get(reverse("quiz:api-categories-export")).json()) == 1

    def test_post_categories(self):
        for i in range(2):
            assert self.client.post(
                reverse("quiz:api-categories-import"),
                content_type="application/json",
                data={
                    "name": f"my-category-{i}",
                    "weight": 3,
                },
            ).status_code == 200
        assert len(self.client.get(reverse("quiz:api-categories-export")).json()) == 2

    def test_post_categories_at_once(self):
        assert self.client.post(
            reverse("quiz:api-categories-import"),
            content_type="application/json",
            data=[
                {"name": "my-cat", "weight": 42},
                {"name": "my-dog", "weight": 123},
            ],
        ).status_code == 200
        assert len(self.client.get(reverse("quiz:api-categories-export")).json()) == 2
