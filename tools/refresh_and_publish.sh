#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
cache="$HOME/.local/share/cb-site-usage"
mkdir -p "$cache/studio-claude"
exec >> "$cache/publish.log" 2>&1
printf '\nUsage refresh started %s\n' "$(date -u +%FT%TZ)"
# Never include pre-existing staged changes in the usage-only commit.
if ! git diff --cached --quiet; then
  printf 'Refusing to publish with pre-existing staged changes\n' >&2
  exit 1
fi
rsync -a --include='*/' --include='*.jsonl' --exclude='*' studio:.claude/projects/ "$cache/studio-claude/"
NEXT_UPDATE_AT="$(python3 -c 'from datetime import datetime,timedelta,time;from zoneinfo import ZoneInfo;z=ZoneInfo("America/Edmonton");n=datetime.now(z);t=datetime.combine(n.date(),time(6,0),z);t=t if t>n else t+timedelta(days=1);print(t.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00","Z"))')"
python3 tools/refresh_usage.py \
  --claude-dirs "$HOME/.claude/projects" "$cache/studio-claude" \
  --ledger "$cache/claude_ledger.json" --out usage.json \
  --next-update-at "$NEXT_UPDATE_AT" \
  --exclude "$HOME/.claude/projects/-Users-xxm-projects-QuantEngine-backup/99aa0798-bbcf-42fb-a10f-d2571f239f85"

git pull --ff-only
if ! git diff --quiet -- usage.json; then
  git add -- usage.json
  git commit -m "Usage snapshot $(date -u +%F)"
  git push
else
  printf 'Usage snapshot unchanged\n'
fi
