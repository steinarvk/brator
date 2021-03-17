from django.test import TestCase

from . import logic

from .testutils import (
    create_regular_user,
    create_numeric_fact,
)

class LargestBatchSizeTest(TestCase):
    def test_get_largest_standard_summarized_batch_size(self):
        user = create_regular_user()
        fact = create_numeric_fact()
        def _answer_n_times(n):
            for i in range(n):
                chal = logic.get_or_create_current_challenge(user)
                logic.respond_to_challenge(user, chal.uid, {
                    "numeric": {
                        "confidence_percent": 90,
                        "ci_low": 40,
                        "ci_high": 60,
                    },
                })
        assert logic.get_largest_standard_summarized_batch_size(user) is None
        _answer_n_times(19)
        assert logic.get_largest_standard_summarized_batch_size(user) is None
        _answer_n_times(1)
        assert logic.get_largest_standard_summarized_batch_size(user) == 20
        _answer_n_times(19)
        assert logic.get_largest_standard_summarized_batch_size(user) == 20
        _answer_n_times(19)
        assert logic.get_largest_standard_summarized_batch_size(user) == 50
