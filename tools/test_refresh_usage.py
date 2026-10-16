"""Offline regression tests; never read real account logs or publish."""
import copy
from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import refresh_usage as usage


class RefreshUsageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / 'logs'
        self.logs.mkdir()
        self.ledger = self.root / 'ledger.json'
        self.out = self.root / 'usage.json'
        self.codex = {'source': 'Codex account usage API', 'updated_at': '2026-10-15T00:00:00Z',
                      'summary': dict.fromkeys(usage.SUMMARY_FIELDS, 100)}
        self.fetch = patch.object(usage, 'fetch_codex', return_value=self.codex).start()
        self.addCleanup(patch.stopall)

    def row(self, identity='a', when='2026-04-25T00:00:00Z', tokens=None):
        return {'type': 'assistant', 'timestamp': when, 'requestId': 'request',
                'message': {'id': identity, 'usage': tokens if tokens is not None else
                            dict(zip(usage.TOKEN_FIELDS, [1, 2, 3, 4]))}}

    def write(self, rows, name='session.jsonl'):
        (self.logs / name).write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def refresh(self, **kwargs):
        return usage.refresh([self.logs], self.ledger, self.out, **kwargs)

    def test_dedup_across_files_and_roots_and_existing_value_unchanged(self):
        self.write([self.row(), self.row()])
        nested = self.logs / 'nested'
        nested.mkdir()
        (nested / 'copy.jsonl').write_text(json.dumps(self.row()) + '\n')
        result = usage.refresh([self.logs, nested], self.ledger, self.out)
        self.assertEqual(result['claude_code']['since_tokens'], 10)
        self.assertEqual(result['claude_code']['since_records'], 1)
        self.write([self.row(tokens={'input_tokens': 999})])
        self.assertEqual(self.refresh()['claude_code']['since_tokens'], 10)

    def test_cutoff_is_strict_and_timezone_aware(self):
        self.write([self.row('before', '2026-04-24T23:59:58Z'),
                    self.row('at', '2026-04-24T23:59:59Z'),
                    self.row('same', '2026-04-25T01:59:59+02:00'),
                    self.row('after', '2026-04-24T23:59:59.001Z')])
        self.assertEqual(self.refresh()['claude_code']['since_records'], 1)

    def test_ledger_retains_deleted_logs_and_adds_new_records(self):
        self.write([self.row()])
        self.refresh()
        (self.logs / 'session.jsonl').unlink()
        self.write([self.row('new', tokens={'output_tokens': 7})])
        result = self.refresh()['claude_code']
        self.assertEqual((result['since_tokens'], result['since_records']), (17, 2))

    def test_invalid_tokens_fail_without_writes(self):
        for value in [True, -1, 1.5, '1', None]:
            with self.subTest(value=value):
                self.write([self.row(tokens={'input_tokens': value})])
                with self.assertRaises(ValueError):
                    self.refresh()
                self.assertFalse(self.out.exists())
                self.assertFalse(self.ledger.exists())

    def test_invalid_codex_fields_and_timestamp(self):
        for field in usage.SUMMARY_FIELDS:
            for value in [True, -1, 1.5, '1', None]:
                data = copy.deepcopy(self.codex)
                data['summary'][field] = value
                self.fetch.return_value = data
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.refresh()
        for value in ['bad', '2026-10-15', None]:
            data = copy.deepcopy(self.codex)
            data['updated_at'] = value
            self.fetch.return_value = data
            with self.assertRaises(ValueError):
                self.refresh()
        self.assertFalse(self.out.exists())
        self.assertFalse(self.ledger.exists())

    def test_malformed_inputs_preserve_existing_files(self):
        self.write([self.row()])
        self.refresh()
        before = (self.out.read_bytes(), self.ledger.read_bytes())
        for content in ['{broken\n', json.dumps(self.row(when='bad')), json.dumps(self.row(identity=None))]:
            (self.logs / 'session.jsonl').write_text(content)
            with self.assertRaises(ValueError):
                self.refresh()
            self.assertEqual((self.out.read_bytes(), self.ledger.read_bytes()), before)
        with self.assertRaises(ValueError):
            usage.refresh([self.root / 'missing'], self.ledger, self.out)

    def test_output_structure_and_next_update(self):
        self.write([self.row()])
        result = self.refresh()
        self.assertEqual(set(result), {'source', 'updated_at', 'summary', 'claude_code', 'generated_at', 'next_update_at'})
        for field in ['source', 'updated_at', 'summary']:
            self.assertEqual(result[field], self.codex[field])
        self.assertEqual(result['claude_code'], {
            'baseline_tokens': 15894738589, 'baseline_until': '2026-04-24',
            'since_tokens': 10, 'since_records': 1, 'total_tokens': 15894738599})
        self.assertEqual(usage.timestamp(result['next_update_at']) - usage.timestamp(result['generated_at']), timedelta(hours=24))
        self.assertEqual(json.loads(self.out.read_text()), result)
        result = self.refresh(next_update_at='2026-10-16T02:00:00+02:00')
        self.assertEqual(result['next_update_at'], '2026-10-16T00:00:00Z')

    def test_bad_ledger_and_schedule_fail(self):
        for ledger in [{}, {'records': []}, {'records': {'bad-key': 1}},
                       {'records': {'["a","b"]': True}}]:
            self.ledger.write_text(json.dumps(ledger))
            with self.assertRaises((ValueError, TypeError)):
                self.refresh()
            self.assertFalse(self.out.exists())
        self.ledger.unlink()
        for hours in [0, -1, float('inf'), float('nan')]:
            with self.assertRaises(ValueError):
                self.refresh(every_hours=hours)
        with self.assertRaises(ValueError):
            self.refresh(next_update_at='bad')
        self.assertFalse(self.ledger.exists())

    def test_staging_failure_leaves_both_files_unchanged(self):
        self.write([self.row()])
        self.refresh()
        before = (self.out.read_bytes(), self.ledger.read_bytes())
        real_stage = usage.stage_json
        def fail_output(path, data):
            if path == self.out:
                raise OSError('simulated disk failure')
            return real_stage(path, data)
        with patch.object(usage, 'stage_json', side_effect=fail_output):
            with self.assertRaises(OSError):
                self.refresh()
        self.assertEqual((self.out.read_bytes(), self.ledger.read_bytes()), before)
        self.assertFalse(list(self.root.glob('.*.json.*')))


if __name__ == '__main__':
    unittest.main()
