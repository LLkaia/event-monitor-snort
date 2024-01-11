from django.test import TestCase
from performance_log.views import PerformanceList
from rest_framework.exceptions import ValidationError
from performance_log.models import Performance
from datetime import timezone
from collections import Counter
from django.utils.timezone import make_aware
import datetime


class TestPerformanceList(TestCase):

    def setUp(self):
        self.log_1 = Performance.objects.create(
            timestamp=make_aware(datetime.datetime(2024, 1, 1), timezone.utc),
            module="binder",
            pegcounts={
                "inspects": 34,
                "new_flows": 22,
                "raw_packets": 12,
                "service_changes": 7
            }
        )

    def test_valid_date_format(self):
        date_str = "2023-01-01 12:00:00"
        result = PerformanceList.validate_date(date_str)
        self.assertIsNotNone(result)
        self.assertEqual(result.strftime("%Y-%m-%d %H:%M:%S"), date_str)

    def test_invalid_date_format(self):
        date_str = "invalid_date"
        with self.assertRaises(ValidationError):
            PerformanceList.validate_date(date_str)

    def test_invalid_params(self):
        entered_params = ['invalid_param']
        allowed_params = ['period_start', 'period_stop', 'module', 'delta']
        with self.assertRaises(ValidationError):
            PerformanceList.validate_params(entered_params, allowed_params)

    def test_valid_params(self):
        entered_params = {'period_start': '2023-01-01',
                          'period_stop': '2023-01-10',
                          'module': 'my_module',
                          'delta': 'true'}
        allowed_params = ['period_start', 'period_stop', 'module', 'delta', 'page']
        PerformanceList.validate_params(entered_params, allowed_params)

    def test_without_param(self):
        entered_params = []
        allowed_params = ['period_start', 'period_stop', 'module', 'delta']
        PerformanceList.validate_params(entered_params, allowed_params)

    def test_get_sum_queryset(self):
        queryset = Performance.objects.filter(module="binder")
        result = PerformanceList.get_sum_queryset(queryset)
        expected_result = [
            {'module': 'binder', 'pegcounts': Counter({
                "inspects": 34,
                "new_flows": 22,
                "raw_packets": 12,
                "service_changes": 7
            })},
        ]
        self.assertEqual(result, expected_result)
