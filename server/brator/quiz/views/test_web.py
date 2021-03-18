from django.test import TestCase
from django.urls import reverse

from ..testutils import create_regular_user, create_fact, create_custom_numeric_fact

from ..models import Challenge, ChallengeFeedback

class IndexTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())

    def test_index(self):
        create_fact()
        resp = self.client.get("/")
        assert resp.status_code == 302

class ChallengeTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())

    def test_challenge(self):
        create_fact()
        resp = self.client.get(reverse("quiz:web-quiz"))
        assert resp.status_code == 200

    def test_get_a_question(self):
        create_custom_numeric_fact(
            "How many roads must a man walk down?",
            4212345
        )
        resp = self.client.get(reverse("quiz:web-quiz"))
        assert resp.status_code == 200
        assert b"How many roads" in resp.content
        assert b"4212345" not in resp.content


    def test_get_a_question_and_answer_it(self):
        create_custom_numeric_fact(
            "How many roads must a man walk down?",
            4212345
        )
        resp = self.client.get(reverse("quiz:web-quiz"))
        assert resp.status_code == 200
        assert b"How many roads" in resp.content
        assert b"4212345" not in resp.content

        challenge = Challenge.objects.first()

        resp = self.client.post(reverse("quiz:web-quiz"), {
            "challenge_uid": challenge.uid,
            "ci_low": "4112345",
            "ci_high": "4312345",
        })
        assert resp.status_code == 302

        resp = self.client.get(reverse("quiz:web-quiz"))
        assert resp.status_code == 200
        assert b"How many roads" in resp.content
        assert b"4212345" in resp.content
        assert b"Correct" in resp.content

    def test_get_a_question_and_answer_it_incorrectly(self):
        create_custom_numeric_fact(
            "How many roads must a man walk down?",
            4212345
        )
        resp = self.client.get(reverse("quiz:web-quiz"))
        assert resp.status_code == 200
        assert b"How many roads" in resp.content
        assert b"4212345" not in resp.content

        challenge = Challenge.objects.first()

        resp = self.client.post(reverse("quiz:web-quiz"), {
            "challenge_uid": challenge.uid,
            "ci_low": "4412345",
            "ci_high": "5012345",
        })
        assert resp.status_code == 302

        resp = self.client.get(reverse("quiz:web-quiz"))
        assert resp.status_code == 200
        assert b"How many roads" in resp.content
        assert b"4212345" in resp.content
        assert b"Incorrect" in resp.content

class EvalTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())

    def test_index(self):
        resp = self.client.get(reverse("quiz:web-eval"))
        assert resp.status_code == 200

class FeedbackTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())
        create_custom_numeric_fact(
            "How many roads must a man walk down?",
            4212345
        )
        self.client.get(reverse("quiz:web-quiz"))
        self.challenge = Challenge.objects.get()

    def test_feedback(self):
        assert ChallengeFeedback.objects.count() == 0
        resp = self.client.post(reverse("quiz:web-feedback"), {
            "challenge_uid": self.challenge.uid,
            "category": "wrong",
            "text": "Answer should be 42",
        })
        assert resp.status_code == 302
        assert ChallengeFeedback.objects.count() == 1

class AccountSettingsTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())

    def test_delete_account(self):
        resp = self.client.get(reverse("quiz:web-account"))
        assert resp.status_code == 200

class DeleteMyAccountTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())
        create_custom_numeric_fact(
            "How many roads must a man walk down?",
            4212345
        )
        self.client.get(reverse("quiz:web-quiz"))
        self.challenge = Challenge.objects.get()

    def test_delete_account(self):
        assert Challenge.objects.count() == 1
        resp = self.client.post(reverse("quiz:web-deleteaccount"), {
            "confirmation_message": "Delete my account. I understand that this action is irreversible.",
        })
        assert Challenge.objects.count() == 0
