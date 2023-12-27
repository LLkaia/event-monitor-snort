import logging
import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()
from monitor.models import Event
from rule.models import Rule


logger = logging.getLogger('monitor')


if __name__ == '__main__':
    Event.objects.all().delete()
    Rule.objects.filter(deprecated=True).delete()
    logger.info('Data base is clear.')
