import json
import logging
import os
import shutil

import django
from django.db.models.deletion import ProtectedError
from django.http import Http404

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()
from rule.models import Rule


logger = logging.getLogger('monitor')
PATH_ORIGINAL_RULES = '/usr/local/etc/rules/pulledpork.rules'
PATH_BACKUP_RULES = '/usr/local/etc/rules/pulledpork.rules_backup'


def dump_rules(file: str) -> int:
    """Save Snort3 Rules into database.

    Dump rules into a file, then get data from file
    and process them.
    :param file: Name of file with rules
    :return: Count of new rules
    """
    exit_code = os.system(
        f"snort -c /usr/local/etc/snort/snort.lua "
        f"--plugin-path=/usr/local/etc/so_rules/ --tweaks custom --dump-rule-meta > {file}")
    if exit_code != 0:
        raise RuntimeError('Dump rules into file was not executed.')

    with open(file, encoding='latin-1') as f:
        data = f.readlines()
    if not data:
        raise RuntimeError('File is empty!')
    count = process_data(data)
    return count


def update_pulledpork_rules():
    """Update Rules

    Run rules updating, check if rules are not malformed
    and then start Snort with new rules.
    """
    # rules backup
    shutil.copy2(
        PATH_ORIGINAL_RULES,
        PATH_BACKUP_RULES
    )

    # update rules
    exit_code = os.system("/usr/local/bin/pulledpork3/pulledpork.py "
                          "-c /usr/local/etc/pulledpork3/pulledpork.conf -q")
    if exit_code != 0:
        raise RuntimeError('Update PulledPork was not executed.')
    logger.info('Update finished')

    # validation run
    exit_code = os.system('snort -c /usr/local/etc/snort/snort.lua '
                          '--plugin-path=/usr/local/etc/so_rules/ --tweaks custom -q')
    if exit_code != 0:
        shutil.move(
            PATH_BACKUP_RULES,
            PATH_ORIGINAL_RULES,
        )
        raise RuntimeError('Rules file malformed.')
    logger.info('Rules are valid.')
    os.remove(PATH_BACKUP_RULES)

    # run snort with new rules
    logger.info('Restarting snort.')
    os.system("supervisorctl restart snort")


def process_data(data: list) -> int:
    """Processing of rules"""
    count = 0

    for line in data:
        rule = json.loads(line)
        try:
            try:
                # if rule exists, skip it
                Rule.get_rule(sid=rule['sid'], rev=rule['rev'], gid=rule['gid'])
                continue
            except Http404:
                # else check if deprecated rules exist and if it
                # does, try to delete them, else mark as deprecated
                deprecated_rules = Rule.objects.filter(sid=rule['sid'], gid=rule['gid'])
                if deprecated_rules:
                    for old_rule in deprecated_rules:
                        try:
                            old_rule.delete()
                        except ProtectedError:
                            old_rule.deprecated = True
                            old_rule.save()
                            logger.info(f'Rule with sid {old_rule.sid} and rev {old_rule.rev} marked as deprecated.')
                # and add new one
                Rule(sid=rule['sid'], rev=rule['rev'], gid=rule['gid'],
                     action=rule['action'], message=rule['msg'], data_json=rule).save()
                count += 1
        except KeyError:
            logger.error(f"Rule's data is not full: {rule}")
    return count


if __name__ == '__main__':
    try:
        count = dump_rules('rules.txt')
        logger.info(f'Added {count} new rules.')
    except RuntimeError as e:
        logger.error(e)
