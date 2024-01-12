from django.test import TestCase
from unittest.mock import patch, MagicMock, call
from unittest import mock
from shell.telnet import run_command, run_profiler
from shell.models import Profiler

HOST = 'localhost'
PORT = 12345


class TelnetTestCase(TestCase):
    @patch('telnetlib.Telnet')
    def test_run_command_success(self, mock_telnet):
        expected_output = "utput"
        mock_tn_instance = MagicMock()
        mock_telnet.return_value.__enter__.return_value = mock_tn_instance
        mock_tn_instance.read_until.side_effect = [b'o")~', 'output\n'.encode('utf-8'), b'o")~']

        result = run_command("host_cache.get_stats()")
        mock_telnet.assert_called_once_with("localhost", 12345)
        expected_call = (
            call(b'o")~')
            if mock_tn_instance.read_until.call_args[1].get('timeout') is None
            else call(b'o")~', timeout=5)
        )

        mock_tn_instance.read_until.assert_has_calls([expected_call], any_order=False)
        mock_tn_instance.write.assert_called_once_with(b'host_cache.get_stats()\n')
        self.assertEqual(result, expected_output)

    @patch('time.sleep')
    @patch('telnetlib.Telnet')
    def test_run_profiler(self, mock_telnet, mock_sleep):
        mock_telnet.return_value.read_until.side_effect = [
            b'o")~',
            b'o")~',
            b'o")~',
            b'o")~',
            b'o")~' + '{"rules": ["rule1", "rule2"]}'.encode('utf-8') + b'o")~',
            b'o")~'
        ]
        mock_telnet.return_value.write.return_value = None

        record = Profiler.objects.create()
        wait = 10

        run_profiler(record, wait)

        mock_telnet.assert_has_calls([
            mock.call(HOST, PORT),

        ])
        mock_sleep.assert_called_once_with(wait)
        self.assertEqual(record.rules, None)
