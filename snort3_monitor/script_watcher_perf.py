import json
import logging
import os
import threading
import time
from json import JSONDecodeError

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()


logger = logging.getLogger('monitor')


class OnMyWatch:
    # watch_directory: str = '/var/log/snort/'
    log_file_pattern: str = 'perf_monitor_base.json'
    # current_position_file: str = '/var/log/snort/current_alerts.txt'
    watch_directory: str = 'C:\\Users\\Kaya\\Desktop\\TaskLPS\\event-monitor-snort\\'
    current_position_file: str = 'C:\\Users\\Kaya\\Desktop\\TaskLPS\\event-monitor-snort\\current_alerts.txt'

    def __init__(self):
        self.lock = threading.Lock()
        self.watch_file = None

    def run(self):
        """Start watch in log file"""
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
        """Open file and read data"""
        try:
            with self.lock:
                with open(self.watch_file, encoding='latin-1') as file:
                    file.seek(self.get_current_position())
                    new_data = file.read()
                    self.save_current_position(file.tell())

                if new_data:
                    self.save_data(new_data)

        except PermissionError:
            logger.error(f'Set up permissions for {self.watch_file}!')
        except FileNotFoundError:
            logger.info('File was deleted.')
            self.watch_file = self.get_latest_file_with_prefix()

    @staticmethod
    def save_data(data: str):
        """Save data into database"""
        data = '[' + data.strip('[],') + ']'
        try:
            data = json.loads(data)
            for line in data:
                print(line)

        except JSONDecodeError as e:
            logger.error(e)

    def get_latest_file_with_prefix(self):
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
