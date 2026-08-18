import json
import logging

from django.test import SimpleTestCase

from common.logging import JsonFormatter


class JsonFormatterTests(SimpleTestCase):
    def setUp(self):
        self.formatter = JsonFormatter()
        self.record = logging.LogRecord(
            name='common.logging.test',
            level=logging.WARNING,
            pathname='mod.py',
            lineno=10,
            msg='hello %s',
            args=('world',),
            exc_info=None,
        )
        self.record.request_id = 'req-123'

    def test_output_is_valid_json_with_core_fields(self):
        payload = json.loads(self.formatter.format(self.record))
        self.assertEqual(payload['level'], 'WARNING')
        self.assertEqual(payload['logger'], 'common.logging.test')
        self.assertEqual(payload['message'], 'hello world')
        self.assertIn('ts', payload)

    def test_extra_attrs_included(self):
        payload = json.loads(self.formatter.format(self.record))
        self.assertEqual(payload['request_id'], 'req-123')
