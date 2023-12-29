from django.test import TestCase
from monitor.views import validate_params
from unittest import mock
from monitor.views import EventListUpdate, error404
from rest_framework.exceptions import ValidationError


class EventListUpdateViewTest(TestCase):

    def test_valid_params(self):
        allowed_params = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'sid', 'proto']
        entered_params = ['src_addr', 'dst_port']

        try:
            validate_params(entered_params, allowed_params)
        except ValidationError:
            self.fail("validate_params raised ValidationError unexpectedly.")

    def test_invalid_params(self):
        allowed_params = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'sid', 'proto']
        entered_params = ['src_addr', 'invalid_param']
        expected_error_message = (
            "You can use only src_addr, src_port, dst_addr, dst_port, sid, proto, page as query filters."
        )
        with self.assertRaises(ValidationError) as context:
            validate_params(entered_params, allowed_params)
        self.assertEqual(str(context.exception.detail['error']), expected_error_message)

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

    def test_error404_with_valid_params(self):
        allowed_params = ['src_addr', 'dst_port']
        entered_params = ['src_addr', 'dst_port']
        response = error404(allowed_params, entered_params)
        self.assertIsNot(response.status_code, 404)

    def test_error404_with_invalid_params(self):
        allowed_params = ['src_addr', 'dst_port']
        entered_params = ['invalid_param']
        response = error404(allowed_params, entered_params)
        self.assertEqual(response.status_code, 404)
