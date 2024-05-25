import logging
import time
from datetime import datetime
from unittest.mock import patch, mock_open

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TransactionTestCase

from monitor.models import Event
from rule.models import Rule


class RuleAPITests(APITestCase):
    fixtures = ['rule.json']

    def test_get_rules(self):
        url = reverse('rules-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_get_filtered_rules_by_one_param(self):
        url = reverse('rules-list') + '?sid=57239'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_filtered_rules_by_three_params(self):
        url = reverse('rules-list') + '?sid=57239&gid=1&rev=1'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_filtered_rule_does_not_exist(self):
        url = reverse('rules-list') + '?sid=57239&gid=2'
        response = self.client.get(url)
        self.assertEqual(len(response.data['results']), 0)


@pytest.mark.slow
class RuleUpdateAPITests(TransactionTestCase):
    logger = logging.getLogger('monitor')

    @patch('rule.views.update_pulledpork_rules', return_value=None)
    @patch('update_rules.os.system', side_effect=(0, 0, 0))
    def test_post_updating_valid_rules(self, patched_system, patched_update):
        with open('rule/fixtures/valid_rules.txt') as f:
            self.valid_rules = f.read()
        url = reverse('rules-create')

        with self.assertLogs(self.logger, level='INFO') as log:
            with patch('update_rules.open', mock_open(read_data=self.valid_rules)):
                self.client.post(url)
            time.sleep(0.2)
            self.assertIn('2 new rules have been added.', log.output[0])

    @patch('rule.views.update_pulledpork_rules', return_value=None)
    @patch('update_rules.os.system', side_effect=(0, 0, 0))
    def test_post_updating_invalid_rules(self, patched_system, patched_update):
        with open('rule/fixtures/invalid_rules.txt') as f:
            self.invalid_rules = f.read()
        url = reverse('rules-create')

        with self.assertLogs(self.logger, level='ERROR') as log:
            with patch('update_rules.open', mock_open(read_data=self.invalid_rules)):
                self.client.post(url)
            time.sleep(0.2)
            self.assertIn("Rule's data is not full:", log.output[0])

    @patch('rule.views.update_pulledpork_rules', return_value=None)
    @patch('update_rules.os.system', side_effect=(0, 0, 0))
    def test_post_rule_with_old_rev(self, patched_system, patched_update):
        Rule.objects.create(**{"gid": 10, "sid": 10, "rev": 1})
        url = reverse('rules-create')

        with self.assertLogs(self.logger, level='INFO') as log:
            with patch('update_rules.open', mock_open(
                    read_data='{"gid": 10, "sid": 10, "rev": 2, "action": "allow", "msg": "smth"}')):
                self.client.post(url)
            time.sleep(0.2)
            rule = Rule.objects.get(sid=10, gid=10)
            self.assertEqual(rule.rev, 2)
            self.assertIn('1 new rules have been added.', log.output[0])

    @patch('rule.views.update_pulledpork_rules', return_value=None)
    @patch('update_rules.os.system', side_effect=(0, 0, 0))
    def test_post_rule_with_old_rev_bind_to_event(self, patched_system, patched_update):
        new_rule = Rule.objects.create(**{"gid": 10, "sid": 10, "rev": 1})
        Event.objects.create(rule=new_rule, timestamp=timezone.now())
        url = reverse('rules-create')

        with self.assertLogs(self.logger, level='INFO') as log:
            with patch('update_rules.open', mock_open(
                    read_data='{"gid": 10, "sid": 10, "rev": 2, "action": "allow", "msg": "smth"}')):
                self.client.post(url)
            time.sleep(0.2)
            self.assertListEqual([True, False], [rule.deprecated for rule in Rule.objects.all()])
            self.assertIn('marked as deprecated.', log.output[0])
