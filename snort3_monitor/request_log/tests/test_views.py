from datetime import datetime
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from request_log.views import RequestList


class TestRequestView(TestCase):

    def test_validate_date(self):
        valid_date_str = '2023-12-26 14:30:00'
        invalid_date_str = 'invalid_date'

        result = RequestList.validate_date(valid_date_str)
        self.assertIsInstance(result, datetime)

        with self.assertRaises(ValidationError) as context:
            RequestList.validate_date(invalid_date_str)
        self.assertEqual(
            str(context.exception),
            "{'error': ErrorDetail(string='Use format YYYY-MM-DD HH:MM:SS (you can skip SS, MM, HH)', code='invalid')}"
        )

    def test_validate_params(self):
        allowed_params = ['period_start', 'period_stop']
        entered_params = ['period_start', 'page']
        RequestList.validate_params(entered_params, allowed_params)
        invalid_params = ['period_start', 'invalid_param']
        with self.assertRaises(ValidationError):
            RequestList.validate_params(invalid_params, allowed_params)
