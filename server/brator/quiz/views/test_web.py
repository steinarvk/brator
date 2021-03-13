from django.test import TestCase
from django.urls import reverse

from ..testutils import create_regular_user

class IndexTest(TestCase):
    def setUp(self):
        self.client.force_login(create_regular_user())

    def test_index(self):
        resp = self.client.get(reverse("quiz:web-index"))
        assert resp.status_code == 200
        assert b"Hello" in resp.content


