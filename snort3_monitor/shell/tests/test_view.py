from unittest.mock import patch
from datetime import timedelta, datetime

from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from django.test import TestCase

from shell.models import Profiler


class ShellCommandTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('shell.views.run_command')
    def test_post_shell_command_success(self, mock_run_command):
        url = reverse('shell-post')
        data = {'command': 'help()'}
        mock_run_command.return_value = "Command output"
        url = reverse('shell-post')
        response = self.client.post(url, {"command": ""})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['message'], 'Provide a command!')

        response = self.client.post(url, data, format='json')
        mock_run_command.assert_called_with('help()')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_empty_param(self):
        url = reverse('shell-post')
        response = self.client.post(url, {"command": ""})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['message'], 'Provide a command!')

    @patch('shell.views.run_command')
    def test_param_rotate(self, mock_run_command):
        url = reverse('shell-post')
        data = {"command": "rotate_stats()"}
        mock_run_command.return_value = "== rotating stats"
        response = self.client.post(url, data, format='json')
        mock_run_command.assert_called_with("rotate_stats()")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"message": "== rotating stats"})

    @patch('shell.views.run_command')
    def test_no_corect_param(self, mock_run_command):
        url = reverse('shell-post')
        data = {"command": "incorect"}
        mock_run_command.return_value = "[string \"shell\"]:1: '=' expected near '<eof>'"
        response = self.client.post(url, data, format='json')
        mock_run_command.assert_called_with("incorect")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "[string \"shell\"]:1: '=' expected near '<eof>'")


class ProfilerTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('shell.views.run_profiler')
    def test_start_rule_profiling_with_time(self, patched_run_profiler):
        url = reverse('start-profiler')
        response = self.client.get(url, {'time': '5'})
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('Rule profiler has been started.', response.data['message'])

    @patch('shell.views.run_profiler')
    def test_start_rule_profiling_with_until(self, patched_run_profiler):
        url = reverse('start-profiler')
        end_time = (datetime.now() + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        response = self.client.get(url, {'until': end_time})
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('Rule profiler has been started.', response.data['message'])

    def test_start_rule_profiling_invalid_time_format(self):
        url = reverse('start-profiler')
        response = self.client.get(url, {'time': 'invalid'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('time', response.data['message'])

    def test_start_rule_profiling_invalid_until_format(self):
        url = reverse('start-profiler')
        response = self.client.get(url, {'until': 'invalid_format'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('until', response.data['message'])

    def test_get_last_profiler_record(self):
        url = reverse('get-profiler')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['message'], 'Profiler records are clear.')

    @patch('shell.views.is_previous_profiler_finished')
    def test_get_last_profiler_record_malformed_record(self, mock_is_previous_profiler_finished):
        mock_is_previous_profiler_finished.side_effect = Profiler.RecordMalformed
        response = self.client.get(reverse('get-profiler'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['message'], 'Previous profiler record was malformed.')

    @patch('shell.views.is_previous_profiler_finished')
    def test_get_last_profiler_record_valid_record(self, mock_is_previous_profiler_finished):
        mock_is_previous_profiler_finished.return_value = Profiler.objects.create(
            start_time=datetime.now(),
            end_time=timezone.now() + timedelta(minutes=5),
            rules=['some_rule']
        )
        response = self.client.get(reverse('get-profiler'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rules', response.data)
        self.assertIsInstance(response.data['rules'], list)

    @patch('shell.views.run_profiler')
    def test_start_rule_profiling_with_zero_duration(self, patched_run_profiler):
        url = reverse('start-profiler')
        response = self.client.get(url, {'time': '0'})

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_start_rule_profiling_with_until_past(self):
        url = reverse('start-profiler')
        end_time = (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        response = self.client.get(url, {'until': end_time})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Provide time in future, not in the past.'})
