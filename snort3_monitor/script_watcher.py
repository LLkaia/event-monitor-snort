import os
import time

import django
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()
from monitor.models import Event


class OnMyWatch:
    watchDirectory = r'/var/log/snort/'

    def __init__(self):
        self.observer = Observer()

    def run(self) -> None:
        event_handler = Handler()
        self.observer.schedule(event_handler,
                               self.watchDirectory,
                               recursive=False
                               )
        self.observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):
    current_position = 0
    queue = True

    def on_any_event(self, event) -> None:
        if not event.src_path.endswith('alert_json.txt'):
            print('Another file')
            return
        elif event.event_type == 'modified' or event.event_type == 'created':
            print('File has changed')
            while True:
                if Handler.queue:
                    Handler.queue = False
                    self.read_data(event)
                    Handler.queue = True
                    break
                time.sleep(1)
        else:
            print(event.event_type)

    @staticmethod
    def read_data(event) -> None:
        try:
            with open(event.src_path, 'r') as file:
                file.seek(Handler.current_position)
                new_data = file.readlines()
                if new_data:
                    Event.create_from_watcher(new_data)
                Handler.current_position = file.tell()
        except (PermissionError, FileNotFoundError):
            pass


if __name__ == '__main__':
    watch = OnMyWatch()
    watch.run()
