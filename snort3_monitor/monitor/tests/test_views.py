from django.test import TestCase
from django.core.exceptions import ValidationError
from monitor.views import validate_params
import unittest
from unittest import mock
from monitor.views import EventListUpdate, error404
from monitor.models import Event, Rule


class EventListUpdateViewTest(TestCase):

    def setUp(self):
        self.rule = Rule.objects.create(
            sid=1,
            gid=1,
            rev=1,
            action="Test Action",
            message="Test Message",
            data_json={"key": "value"}
        )
        self.event1 = Event.objects.create(
            rule=self.rule,
            timestamp='2023-12-27 16:01:00',
            src_addr='192.168.1.1',
            dst_addr='192.168.1.2',
            proto='TCP'
        )
        self.event2 = Event.objects.create(
            rule=self.rule,
            timestamp='2023-12-28 10:30:00',
            src_addr='192.168.1.3',
            dst_addr='192.168.1.4',
            proto='UDP'
        )

    def test_valid_params(self):
        allowed_params = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'sid', 'proto']
        entered_params = ['src_addr', 'dst_port']

        try:
            validate_params(entered_params, allowed_params)
        except ValidationError:
            self.fail("validate_params raised ValidationError unexpectedly.")

    @unittest.skip
    def test_invalid_params(self):
        allowed_params = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'sid', 'proto']
        entered_params = ['src_addr', 'invalid_param']

        with self.assertRaises(ValidationError) as context:
            validate_params(entered_params, allowed_params)

        self.assertEqual(
            context.exception.message,
            {
                "error": "Invalid query parameters: invalid_param. "
                         "Allowed parameters are: src_addr, src_port, dst_addr, dst_port, sid, proto, page."
            }
        )

    def test_valid_params_empty(self):
        allowed_params = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'sid', 'proto']
        entered_params = []

        result = validate_params(entered_params, allowed_params)
        self.assertIsNone(result)

    def test_get_queryset_error(self):
        with mock.patch('monitor.views.Event.objects.filter', side_effect=Exception()):
            with self.assertRaises(Exception):
                EventListUpdate.get_queryset({})

    def test_error404_handler_with_param(self):
        allowed_params = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'sid', 'proto']
        entered_params = ['src_addr', 'dst_port']
        response = error404(allowed_params, entered_params)
        self.assertIsNot(response.status_code, 404)

    def test_error404_handler(self):
        response = error404(None, None)
        self.assertEqual(response.status_code, 404)
