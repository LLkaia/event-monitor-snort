from django.test import TestCase
from performance_log.serializers import PerformanceSerializer
from performance_log.models import Performance


class SerializrTest(TestCase):

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

    def test_all_result(self):
        serializer = PerformanceSerializer(self.log_1)
        serializer_data = serializer.data
        self.assertEqual(len(serializer_data), 2)

    def test_module(self):
        serializer = PerformanceSerializer(self.log_1)
        serializer_data = serializer.data
        self.assertEqual(serializer_data['module'], 'binder')

    def test_pegcounts(self):
        serializer = PerformanceSerializer(self.log_1)
        serializer_data = serializer.data
        self.assertEqual(len(serializer_data['pegcounts']), 4)
        expected_pegcounts = {"inspects": 34, "new_flows": 22, "raw_packets": 12, "service_changes": 7}
        self.assertEqual(serializer_data['pegcounts'], expected_pegcounts)
