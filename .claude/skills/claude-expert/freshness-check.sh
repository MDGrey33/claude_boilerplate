#!/usr/bin/env bash
# claude-expert lazy freshness gate.
# Prints STALE if claude-expert hasn't researched in >=7 days and no fresh lock is
# held; prints FRESH otherwise. A STALE result CLAIMS a 2-hour lock so concurrent
# invocations don't spawn duplicate refreshes. The background refresh subagent must,
# on completion, write today's date to .last-research and `rm -f` the lock.
set -euo pipefail
# Self-locate: resolve this script's own dir so the gate works for user-level
# (~/.claude/skills/...) AND project-level (./.claude/skills/...) installs alike.
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || SELF_DIR="."
DIR="${SELF_DIR:-.}"
STAMP="$DIR/.last-research"
LOCK="$DIR/.research-lock"
THRESHOLD_DAYS=7
LOCK_TTL=7200   # 2h — a crashed refresh auto-unlocks so it retries later

# `stamp` subcommand — a completed refresh marks itself fresh in the SAME
# self-located dir the gate reads, so the two halves never disagree on location.
if [ "${1:-}" = "stamp" ]; then
  date +%F > "$STAMP"; rm -f "$LOCK"
  echo "stamped: $STAMP=$(cat "$STAMP" 2>/dev/null), lock cleared"
  exit 0
fi

now=$(date +%s)
last_date=$(cat "$STAMP" 2>/dev/null || echo "1970-01-01")
# Portable epoch parse: BSD/macOS (`date -j -f`) first, then GNU/Linux (`date -d`), else 0.
last=$(date -j -f "%Y-%m-%d" "$last_date" +%s 2>/dev/null || date -d "$last_date" +%s 2>/dev/null || echo 0)
age=$(( (now - last) / 86400 ))

# Respect a fresh in-progress lock.
if [ -f "$LOCK" ]; then
  lock_ts=$(cat "$LOCK" 2>/dev/null || echo 0)
  case "$lock_ts" in (''|*[!0-9]*) lock_ts=0;; esac
  if [ $(( now - lock_ts )) -lt "$LOCK_TTL" ]; then
    echo "FRESH (refresh already in progress; last_research=${last_date}, age=${age}d)"
    exit 0
  fi
fi

if [ "$age" -ge "$THRESHOLD_DAYS" ]; then
  echo "$now" > "$LOCK"   # claim the run
  echo "STALE (last_research=${last_date}, age=${age}d) — spawn the background refresh now"
else
  echo "FRESH (last_research=${last_date}, age=${age}d)"
fi
