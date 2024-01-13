import logging
from datetime import datetime
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils.timezone import make_aware

from shell.telnet import run_command, run_profiler
from shell.models import Profiler


class TelnetTestCase(TestCase):
    def setUp(self) -> None:
        self.HOST = 'localhost'
        self.PORT = 12345
        self.logger = logging.getLogger('monitor')

    @patch('telnetlib.Telnet')
    def test_run_command_success(self, mock_telnet):
        expected_value = "modules commands"
        mock_tn = MagicMock()
        mock_telnet.return_value.__enter__.return_value = mock_tn
        mock_tn.read_until.side_effect = (None, 'modules commandso")~\n'.encode('utf-8'))
        result = run_command('help()')
        mock_telnet.assert_called_with(self.HOST, self.PORT)
        self.assertEqual(result, expected_value)

    @patch('time.sleep')
    @patch('telnetlib.Telnet')
    def test_run_profiler(self, mock_telnet, mock_sleep):
        profiler = Profiler.objects.create(
            start_time=make_aware(datetime.fromtimestamp(1705152575)),
            end_time=make_aware(datetime.fromtimestamp(1705153963))
        )
        profiler_rules = """
        { "startTime": 1705152575, "endTime": 1705153963, "rules": [
        {
            "gid": 1, "sid": 1676, "rev": 7, "checks": 63524, "matches": 0, "alerts": 0,
            "timeUs": 104216, "avgCheck": 1, "avgMatch": 0, "avgNonMatch": 1, "timeouts": 0,
            "suspends": 0, "ruleTimePercentage": 0.00751
        }]}
        """
        mock_tn = MagicMock()
        mock_telnet.return_value.__enter__.return_value = mock_tn
        mock_tn.read_until.side_effect = (None, None, None, profiler_rules.encode('utf-8'))
        with self.assertLogs(self.logger, level='INFO') as log:
            run_profiler(profiler, 60)
            mock_telnet.assert_called_with(self.HOST, self.PORT)
            self.assertEqual(profiler.rules[0].get('gid'), 1)
            self.assertIn('Rule profiler entered.', log.output[0])
            self.assertIn('Rule profiler finished.', log.output[1])
