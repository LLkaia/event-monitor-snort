import json
import logging
import os
import threading
import time
from datetime import datetime
from json import JSONDecodeError

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()
from performance_log.models import Performance


logger = logging.getLogger('monitor')


class OnMyWatch:
    watch_directory: str = '/var/log/snort/'
    log_file_pattern: str = 'perf_monitor_base.json'
    current_position_file: str = '/var/log/snort/current_perf.txt'
    # watch_directory: str = 'C:\\Users\\Kaya\\Desktop\\TaskLPS\\event-monitor-snort\\'
    # current_position_file: str = 'C:\\Users\\Kaya\\Desktop\\TaskLPS\\event-monitor-snort\\current_alerts.txt'

    def __init__(self):
        self.lock = threading.Lock()
        self.watch_file = None

    def run(self):
        """Start watch into a log file

        For current watch file check for updates every 60 seconds,
        also check for new file creation every 5 min.
        """
        logger.info('Running.')
        try:
            i = 0
            while True:
                if self.watch_file:
                    self.read_data()
                    i += 1
                    if i == 5:
                        self.watch_file = self.get_latest_file_with_prefix()
                        i = 0
                else:
                    self.watch_file = self.get_latest_file_with_prefix()
                    if self.watch_file:
                        continue
                    else:
                        logger.info('There is no file match with pattern.')
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info('Stopped.')

    def read_data(self):
        """Open file, read and prepare data"""
        try:
            with self.lock:
                with open(self.watch_file, encoding='latin-1') as file:
                    file.seek(self.get_current_position())
                    new_data = file.read()
                    self.save_current_position(file.tell())
                new_data = new_data.strip('[],\n ')
                if new_data:
                    self.save_data('[' + new_data + ']')
                else:
                    self.watch_file = self.get_latest_file_with_prefix()
        except PermissionError:
            logger.error(f'Set up permissions for {self.watch_file}!')
        except FileNotFoundError:
            logger.info('File was deleted.')
            self.watch_file = self.get_latest_file_with_prefix()

    @staticmethod
    def save_data(data: str):
        """Save data into a database"""
        try:
            data = json.loads(data)
            for record in data:
                timestamp = datetime.fromtimestamp(record.pop('timestamp'))
                for module, pegcounts in record.items():
                    Performance.objects.create(timestamp=timestamp, module=module, pegcounts=pegcounts)
        except JSONDecodeError as e:
            logger.error(e)

    def get_latest_file_with_prefix(self):
        """Check if new file was created"""
        files = []
        for f in os.listdir(self.watch_directory):
            if f.startswith(self.log_file_pattern):
                files.append(os.path.join(self.watch_directory, f))
        if not files:
            return None
        files.sort(key=lambda x: os.path.getctime(x), reverse=True)

        if files[0] != self.watch_file:
            self.save_current_position(0)
            logger.info(f'Switched to file "{files[0]}"')

        return files[0]

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
