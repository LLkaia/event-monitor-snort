from unittest.mock import patch
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse


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
