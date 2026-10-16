#!/usr/bin/env python3
"""Refresh public aggregate usage from Codex and retained Claude Code logs."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from urllib.request import Request, urlopen

API_URL = 'https://codefolio-dark-portfolio.derrick-xu84.chatgpt.site/api/usage'
BASELINE_TOKENS = 15_894_738_589
CUTOFF = datetime(2026, 4, 24, 23, 59, 59, tzinfo=timezone.utc)
SUMMARY_FIELDS = ('lifetimeTokens', 'peakDailyTokens', 'longestRunningTurnSec',
                  'longestStreakDays', 'currentStreakDays')
TOKEN_FIELDS = ('input_tokens', 'output_tokens', 'cache_creation_input_tokens',
                'cache_read_input_tokens')


def nonnegative_int(value):
    if type(value) is not int or value < 0:
        raise ValueError('Expected a nonnegative integer')
    return value


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Expected an ISO timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp must include a timezone')
    return parsed.astimezone(timezone.utc)


def utc_iso(value):
    return value.isoformat().replace('+00:00', 'Z')


def fetch_codex():
    request = Request(API_URL, headers={"User-Agent": "derrickxxm-site-usage-refresh/1.0", "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def validate_codex(data):
    if not isinstance(data, dict) or not isinstance(data.get('source'), str) or not data['source'].strip():
        raise ValueError('Missing Codex source')
    timestamp(data['updated_at'])
    for field in SUMMARY_FIELDS:
        nonnegative_int(data['summary'][field])


EXCLUDED = set()  # explicit --exclude paths (printed in the summary), never silent


def collect_records(directories, ledger):
    if not isinstance(ledger, dict) or not isinstance(ledger.get('records'), dict):
        raise ValueError('Invalid ledger structure')
    records = dict(ledger['records'])
    for key, tokens in records.items():
        identity = json.loads(key)
        if not isinstance(identity, list) or len(identity) not in (1, 2) or not all(isinstance(v, str) and v for v in identity):
            raise ValueError('Invalid ledger identity')
        nonnegative_int(tokens)
    for directory in directories:
        root = Path(directory)
        if not root.is_dir():
            raise ValueError(f'Claude directory missing: {root}')
        # os.walk with onerror prevents unreadable subtrees being silently skipped.
        def walk_error(error):
            raise error
        for folder, subdirs, filenames in os.walk(root, onerror=walk_error):
            subdirs[:] = sorted(d for d in subdirs if str(Path(folder) / d) not in EXCLUDED)
            for filename in sorted(filenames):
                if not filename.endswith('.jsonl'):
                    continue
                path = Path(folder) / filename
                with path.open(encoding='utf-8') as stream:
                    for number, line in enumerate(stream, 1):
                        try:
                            row = json.loads(line)
                            if not isinstance(row, dict):
                                raise ValueError('Expected a JSON object')
                            if row.get('type') != 'assistant':
                                continue
                            message = row.get('message')
                            if not isinstance(message, dict):
                                raise ValueError('Invalid assistant message')
                            if 'usage' not in message:
                                continue
                            usage = message['usage']
                            if not isinstance(usage, dict):
                                raise ValueError('Invalid usage')
                            tokens = sum(nonnegative_int(usage.get(field, 0)) for field in TOKEN_FIELDS)
                            recorded_at = timestamp(row['timestamp'])
                            if recorded_at <= CUTOFF:
                                continue
                            identity = [message['id']] + ([row['requestId']] if 'requestId' in row else [])
                            if not all(isinstance(v, str) and v for v in identity):
                                raise ValueError('Missing usage identity')
                            key = json.dumps(identity, separators=(',', ':'), ensure_ascii=False)
                            records.setdefault(key, tokens)
                        except (ValueError, KeyError, TypeError) as error:
                            raise ValueError(f'{path}:{number}: {error}') from error
    return {'records': records}


def stage_json(path, data):
    """Create a complete, flushed sibling file; the caller replaces only after staging."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise
    return Path(name)


def refresh(directories, ledger_path, out_path, next_update_at=None, every_hours=24):
    ledger_path, out_path = Path(ledger_path), Path(out_path)
    if ledger_path.resolve() == out_path.resolve():
        raise ValueError('Ledger and output must be different paths')
    if not math.isfinite(every_hours) or every_hours <= 0:
        raise ValueError('--every-hours must be positive and finite')
    data = fetch_codex()
    validate_codex(data)
    ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {'records': {}}
    ledger = collect_records(directories, ledger)
    generated = datetime.now(timezone.utc)
    next_update = timestamp(next_update_at) if next_update_at is not None else generated + timedelta(hours=every_hours)
    since_tokens = sum(ledger['records'].values())
    output = {key: data[key] for key in ('source', 'updated_at', 'summary')}
    output.update(claude_code={
        'baseline_tokens': BASELINE_TOKENS, 'baseline_until': '2026-04-24',
        'since_tokens': since_tokens, 'since_records': len(ledger['records']),
        'total_tokens': BASELINE_TOKENS + since_tokens,
    }, generated_at=utc_iso(generated), next_update_at=utc_iso(next_update))
    staged = []
    try:
        staged.append(stage_json(ledger_path, ledger))
        staged.append(stage_json(out_path, output))
        # Ledger first: if output replacement fails, retry retains all accumulated usage.
        os.replace(staged[0], ledger_path)
        os.replace(staged[1], out_path)
    finally:
        for path in staged:
            path.unlink(missing_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claude-dirs', nargs='+', required=True)
    parser.add_argument('--ledger', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--next-update-at')
    parser.add_argument('--every-hours', type=float, default=24)
    parser.add_argument('--exclude', nargs='*', default=[], help='directories to skip explicitly (listed in output)')
    args = parser.parse_args()
    EXCLUDED.update(str(Path(p).expanduser()) for p in args.exclude)
    try:
        result = refresh(args.claude_dirs, args.ledger, args.out, args.next_update_at, args.every_hours)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f'Usage refresh failed: {error}', file=sys.stderr)
        return 1
    claude = result['claude_code']
    print(f"excluded: {sorted(EXCLUDED)} | Codex {result['summary']['lifetimeTokens']} | Claude Code {claude['total_tokens']} ({claude['since_records']} accumulated records) | next {result['next_update_at']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
