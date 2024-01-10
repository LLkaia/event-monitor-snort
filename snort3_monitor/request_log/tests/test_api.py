from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from request_log.models import Request
from django.utils import timezone
from datetime import datetime, timedelta


class TestApiRequest(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fixed_timestamp = timezone.now()

    def setUp(self):
        self.request_1 = Request.objects.create(
            user_addr="172.18.0.1",
            http_method="GET",
            timestamp=self.fixed_timestamp,
            endpoint="/api/v1/requests-log/",
            response=400,
            request_data={
                "period_sop": "2023-12-28 14:46:03",
                "period_start": "2023-12-27 13:45:40"
            }
        )

        self.request_2 = Request.objects.create(
            user_addr="172.18.0.1",
            http_method="GET",
            timestamp=self.fixed_timestamp,
            endpoint="/api/v1/requests-log",
            response=404,
            request_data={
                "period_sop": "2023-12-08 11:35:04",
                "period_start": "2023-12-04 11:36:07"
            }
        )

        self.request_3 = Request.objects.create(
            user_addr="172.18.0.1",
            http_method="GET",
            timestamp=self.fixed_timestamp,
            endpoint="/api/v1/events/count",
            response=404,
            request_data={
                "type": "sid",
                "period": "all"
            }
        )

    def test_request_list_with_two_objects(self):
        current_datetime = datetime.now()
        period_start = (current_datetime - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        period_stop = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        url = reverse('request-list')
        response = self.client.get(url, {'period_start': period_start, 'period_stop': period_stop})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 3)

    def test_request_list_with_invalid_date_format(self):
        url = reverse('request-list')
        response = self.client.get(url, {'period_start': 'invalid_date_format'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_missing_parameters(self):
        url = reverse('request-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "You should define 'period_start' and 'period_stop'.")

    def test_request_list_id_order(self):
        current_datetime = datetime.now()
        period_start = (current_datetime - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        period_stop = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        url = reverse('request-list')
        response = self.client.get(url, {'period_start': period_start, 'period_stop': period_stop})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

        results = response.data['results']
        self.assertEqual(len(results), 3)
        ids = [result['id'] for result in results]
        self.assertEqual(ids, sorted(ids))

    def test_request_list_weak(self):
        current_datetime = datetime.now()
        period_start = (current_datetime - timedelta(days=8)).strftime('%Y-%m-%d %H:%M:%S')
        period_stop = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

        url = reverse('request-list')
        response = self.client.get(url, {'period_start': period_start, 'period_stop': period_stop})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "The range has to be less than a week")
