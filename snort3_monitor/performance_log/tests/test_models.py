from django.test import TestCase
from performance_log.models import Performance


class PerformanceModelTest(TestCase):

    def setUp(self):
        self.log_1 = Performance.objects.create(
            timestamp='2024-01-01',
            module="binder",
            pegcounts={
                "inspects": 34,
                "new_flows": 22,
                "raw_packets": 12,
                "service_changes": 7
            }
        )

    def test_timestamp(self):
        self.assertEqual(self.log_1.timestamp, '2024-01-01')

    def test_module(self):
        self.assertEqual(self.log_1.module, "binder")
        self.assertIsInstance(self.log_1.module, str)

    def test_field_response(self):
        self.assertIsInstance(self.log_1.timestamp, str)
        field_label = self.log_1._meta.get_field('module').verbose_name
        self.assertEqual(field_label, 'module')

    def test_pegcounts(self):
        self.assertEqual(self.log_1.pegcounts, {'inspects': 34,
                                                'new_flows': 22,
                                                'raw_packets': 12,
                                                'service_changes': 7})
