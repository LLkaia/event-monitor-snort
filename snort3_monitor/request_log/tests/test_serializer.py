from django.test import TestCase
from request_log.serializers import RequestSerializer
from request_log.models import Request
from django.utils import timezone


class RequestSerializerTest(TestCase):

    def setUp(self):
        self.request_1 = Request.objects.create(
            user_addr="172.18.0.1",
            http_method="GET",
            timestamp=timezone.now(),
            endpoint="/api/v1/rules/",
            response=200,
            request_data={}
        )

    def test_timestamp(self):
        serializer = RequestSerializer(self.request_1)
        serializer_data = serializer.data
        serializer_timestamp = timezone.datetime.fromisoformat(serializer_data["timestamp"])
        self.assertEqual(serializer_timestamp, self.request_1.timestamp)

    def test_http_method(self):
        serializer = RequestSerializer(self.request_1)
        serializer_data = serializer.data
        self.assertEqual(serializer_data["http_method"], self.request_1.http_method)

    def test_endpoint(self):
        serializer = RequestSerializer(self.request_1)
        serializer_data = serializer.data
        self.assertEqual(serializer_data["endpoint"], self.request_1.endpoint)

    def test_response(self):
        serializer = RequestSerializer(self.request_1)
        serializer_data = serializer.data
        self.assertIsInstance(serializer_data['response'], int)

    def test_deserialization(self):
        valid_data = {
            'user_addr': '127.0.0.1',
            'http_method': 'GET',
            'timestamp': '2023-12-26T10:17:31.480206',
            'endpoint': '/api/v1/test/',
            'response': 200,
            'request_data': {}}
        serializer = RequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        deserialized_instance = serializer.save()
        self.assertIsInstance(deserialized_instance, Request)
