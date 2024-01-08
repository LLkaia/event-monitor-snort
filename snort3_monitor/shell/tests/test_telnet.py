from django.test import TestCase
from unittest.mock import patch, MagicMock
from shell.telnet import run_command
from unittest.mock import call


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
