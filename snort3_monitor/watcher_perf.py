import json
import logging
import os
import threading
import time
from datetime import datetime
from json import JSONDecodeError

import django
from django.utils.timezone import make_aware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()
from performance_log.models import Performance


logger = logging.getLogger('monitor')


class OnMyWatch:
    log_file: str = '/var/log/snort/perf_monitor_base.json'
    current_position_file: str = '/var/log/snort/current_perf.txt'

    def __init__(self):
        self.lock = threading.Lock()
        self.log_size = 0

    def run(self):
        """Watch into a log file"""
        logger.info('Performance watcher running.')
        try:
            while True:
                try:
                    self.check_if_file_was_replaced()
                    self.read_data()
                except FileNotFoundError:
                    logger.error(f'{self.log_file} does not exist.')
                finally:
                    time.sleep(20)
        except KeyboardInterrupt:
            logger.info('Performance watcher stopped.')

    def read_data(self):
        """Open file, read and prepare data for saving"""
        try:
            with self.lock:
                with open(self.log_file, encoding='latin-1') as file:
                    file.seek(self.get_current_position())
                    new_data = file.read()
                    self.save_current_position(file.tell())
                new_data = new_data.strip('[],\n ')
                if new_data:
                    self.save_data('[' + new_data + ']')
        except PermissionError:
            logger.error(f'Set up permissions for {self.log_file}!')

    @staticmethod
    def save_data(data: str):
        """Save data into a database"""
        try:
            data = json.loads(data)
            for record in data:
                timestamp = make_aware(datetime.fromtimestamp(record.pop('timestamp')))
                for module, pegcounts in record.items():
                    Performance.objects.create(timestamp=timestamp, module=module, pegcounts=pegcounts)
        except JSONDecodeError as e:
            logger.error(e)

    def check_if_file_was_replaced(self):
        """Check if new file was created and update log size"""
        new_log_size = os.path.getsize(self.log_file)
        if new_log_size < self.log_size:
            self.save_current_position(0)
            logger.info('Switched to a new file')
        self.log_size = new_log_size

    @classmethod
    def get_current_position(cls) -> int:
        """Get current position from file if it already exists."""
        try:
            with open(cls.current_position_file, 'r') as f:
                return int(f.read().strip())
        except FileNotFoundError:
            return 0

    @classmethod
    def save_current_position(cls, position: int):
        """Save current position"""
        with open(cls.current_position_file, 'w') as f:
            f.write(str(position))


if __name__ == '__main__':
    watcher = OnMyWatch()
    watcher.run()
