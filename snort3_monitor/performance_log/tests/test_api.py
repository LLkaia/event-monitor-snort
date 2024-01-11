from rest_framework.test import APITestCase
from performance_log.models import Performance
from django.urls import reverse
from rest_framework import status
from django.utils import timezone


class TestApiPerformance(APITestCase):

    def setUp(self):
        self.log_1 = Performance.objects.create(
            timestamp=timezone.make_aware(timezone.datetime(2024, 1, 2, 13, 3, 26, 683246)),
            module="binder",
            pegcounts={
                "inspects": 34,
                "new_flows": 22,
                "raw_packets": 12,
                "service_changes": 7
            }
        )

        self.log_2 = Performance.objects.create(
            timestamp=timezone.make_aware(timezone.datetime(2024, 1, 3, 13, 3, 26, 683246)),
            module="pref_monitor",
            pegcounts={
                "inspects": 37,
                "new_flows": 20,
                "raw_packets": 11,
                "service_changes": 8
            }
        )

        self.log_3 = Performance.objects.create(
            timestamp=timezone.make_aware(timezone.datetime(2024, 1, 7, 13, 3, 26, 653244)),
            module="binder",
            pegcounts={
                "inspects": 35,
                "new_flows": 21,
                "raw_packets": 82,
                "service_changes": 3
            }
        )

    def test_with_out_time(self):
        url = reverse("performance-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_with_out_time_error(self):
        url = reverse("performance-list")
        response = self.client.get(url)
        self.assertIn('error', response.data)
        self.assertIsInstance(response.data['error'], str)

    def test_by_all_time(self):

        url = reverse("performance-list")
        response = self.client.get(url, {"period_start": "2024-01-10", "period_stop": "2024-01-12"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_by_all_H_M_S(self):
        url = reverse("performance-list")
        response = self.client.get(url, {"period_start": "2024-01-10 13:03:26", "period_stop": "2024-01-12 13:03:26"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_with_modules(self):
        url = reverse("performance-list")
        response = self.client.get(url, {"period_start": "2024-01-01", "period_stop": "2024-01-08",
                                         "module": "binder"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_invalid_params(self):
        url = reverse('performance-list')
        response = self.client.get(url, {
            'invalid_param': 'value'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "error": "You can use only period_start, period_stop, module, delta, page as query filters."
        })

    def test_by_page(self):
        url = reverse("performance-list")
        response = self.client.get(url, {"page": 1, "period_start": "2024-01-01", "period_stop": "2024-01-08"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        expected_results = 3
        self.assertEqual(len(response.data['results']), expected_results)
