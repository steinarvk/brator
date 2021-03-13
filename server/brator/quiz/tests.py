import pytest
from django.test import TestCase

from .logic import (
    select_random_fact,
    post_fact,
)
from .testutils import DUMMY_FACT_DATA

class SelectFactTests(TestCase):

    def test_select_nonexistent_fact(self):
        assert select_random_fact() is None

    def test_create_and_select_fact(self):
        post_fact(DUMMY_FACT_DATA[0])
        assert select_random_fact().key == "human-legs"
