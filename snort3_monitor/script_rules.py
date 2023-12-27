import json
import logging
import os

import django
from django.db.models.deletion import ProtectedError


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()
from rule.models import Rule


logger = logging.getLogger('monitor')


def update_pulled_pork(file: str) -> int:
    """Update Snort3 rules

    Update rules with PulledPork3 and dump them into a file, get
    data from file and process it. Reload Snort3 when update ends.

    :param file: Name of file with rules
    :return: Count of new rules
    """
    # update rules
    exit_code = os.system("/usr/local/bin/pulledpork3/pulledpork.py -c /usr/local/etc/pulledpork3/pulledpork.conf")
    if exit_code != 0:
        raise RuntimeError('Update PulledPork was not executed.')

    # dump rules
    exit_code = os.system(
        f"snort -c /usr/local/etc/snort/snort.lua "
        f"--plugin-path=/usr/local/etc/so_rules/ --dump-rule-meta --tweaks custom > {file}")
    if exit_code != 0:
        raise RuntimeError('Dump rules into file was not executed.')

    with open(file, encoding='latin-1') as f:
        data = f.readlines()
    if not data:
        raise RuntimeError('File is empty!')
    count = process_data(data)

    os.system("supervisorctl restart snort")

    return count


def process_data(data: list) -> int:
    """Processing of rules"""
    count = 0

    for line in data:
        rule = json.loads(line)
        try:
            # checking if rule exists
            deprecated_rules = Rule.objects.filter(sid=rule['sid'], gid=rule['gid'])

            # If old rules exists, try to delete them, else mark as deprecated and finally add new one
            # If there are rules with same rev, skip them
            if deprecated_rules:
                for old_rule in deprecated_rules:
                    if old_rule.rev < rule['rev']:
                        try:
                            old_rule.delete()
                        except ProtectedError:
                            old_rule.deprecated = True
                            old_rule.save()
                            logger.info(f'Rule with sid {old_rule.sid} and {old_rule.rev} marked as deprecated.')
                        finally:
                            Rule(sid=rule['sid'], rev=rule['rev'], gid=rule['gid'],
                                 action=rule['action'], message=rule['msg'], data_json=rule).save()
                            count += 1
                    else:
                        continue
            else:
                # creating new rule if it does not exist
                Rule(sid=rule['sid'], rev=rule['rev'], gid=rule['gid'],
                     action=rule['action'], message=rule['msg'], data_json=rule).save()
                count += 1
        except KeyError:
            logger.error(f"Rule's data is not full: {rule}")
    return count


if __name__ == '__main__':
    try:
        count = update_pulled_pork('rules.txt')
        logger.info(f'Added {count} new rules.')
    except RuntimeError as e:
        logger.error(e)
