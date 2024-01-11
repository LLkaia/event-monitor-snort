from django.test import TestCase
from performance_log.models import Performance
from django.utils import timezone


class PerformanceModelTest(TestCase):

    def setUp(self):
        self.log_1 = Performance.objects.create(
            timestamp=timezone.now(),
            module="binder",
            pegcounts={
                "inspects": 34,
                "new_flows": 22,
                "raw_packets": 12,
                "service_changes": 7
            }
        )

    def test_timestamp(self):
        self.assertIsNotNone(self.log_1.timestamp)

    def test_module(self):
        self.assertEqual(self.log_1.module, "binder")
        self.assertIsInstance(self.log_1.module, str)

    def test_field_response(self):
        field_label = self.log_1._meta.get_field('module').verbose_name
        self.assertEqual(field_label, 'module')

    def test_pegcounts(self):
        self.assertEqual(self.log_1.pegcounts, {'inspects': 34,
                                                'new_flows': 22,
                                                'raw_packets': 12,
                                                'service_changes': 7})
