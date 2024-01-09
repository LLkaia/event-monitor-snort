import json
import telnetlib
import time
import logging
from json import JSONDecodeError

from shell.models import Profiler

HOST = "localhost"
PORT = 12345
shell_invite_character = b'o")~'

logger = logging.getLogger('monitor')


def run_command(command: str) -> str:
    """Run command in snort shell and return stdout"""
    command = command.encode('utf-8')
    with telnetlib.Telnet(HOST, PORT) as tn:
        tn.read_until(shell_invite_character)
        tn.write(command + b'\n')
        output = tn.read_until(shell_invite_character, timeout=5)
    return output.decode('utf-8').strip('o")~\n ')


def run_profiler(record: Profiler, wait: int) -> None:
    """Run profiler through snort shell.

    Take 'record' object and period for profiling,
    start profiler, wait til the end, then write
    result into given 'record' object.
    """
    with telnetlib.Telnet(HOST, PORT) as tn:
        tn.read_until(shell_invite_character)
        tn.write('profiler.rule_stop()'.encode('utf-8') + b'\n')
        tn.read_until(shell_invite_character)
        tn.write('profiler.rule_start()'.encode('utf-8') + b'\n')
    logger.info('Rule profiler entered.')
    time.sleep(wait)
    with telnetlib.Telnet(HOST, PORT) as tn:
        tn.read_until(shell_invite_character)
        tn.write("profiler.rule_dump('json')".encode('utf-8') + b'\n')
        output = tn.read_until(shell_invite_character, timeout=5).decode('utf-8').strip('o")~\n ')
        tn.write('profiler.rule_stop()'.encode('utf-8') + b'\n')
    try:
        rules = json.loads(output).get('rules')
        record.rules = rules
        record.save()
        logger.info('Rule profiler finished.')
    except (TypeError, JSONDecodeError) as e:
        logger.error(e)
