#!/usr/bin/env bash
# Fetch received emails from Outlook Web by driving a headless Chromium
# session under this skill's persistent browser profile. Emits a JSON array
# of conversations (each with its extracted messages) on stdout.
#
# No admin-consent flows, no Graph API tokens. Uses whatever Outlook session
# you logged into once via scripts/outlook_login.sh.
#
# Usage:
#   fetch_emails.sh [hours-back] [query]
#
#   hours-back : how far back to scan the inbox list (default 24 — i.e. today)
#   query      : optional Outlook search query; when set, scrapes the search
#                results instead of the chronological inbox (hours filter is
#                then only advisory)
#
# Env overrides:
#   FETCH_DEBUG=1        — verbose logging to stderr
#   FETCH_HEADED=1       — open a visible browser window (debugging)
#   FETCH_TIMEOUT_MS=<n> — per-navigation timeout (default 60000)
#   FETCH_MAX=<n>        — max conversations to open (default 25)
#   FETCH_ALL=1          — skip filters.json noise filtering

set -euo pipefail

HOURS_BACK="${1:-24}"
QUERY="${2:-}"

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_DIR="$SKILL_DIR/.browser-profile"

if [[ ! -d "$PROFILE_DIR" ]]; then
  cat >&2 <<EOF
ERROR: browser profile not found at $PROFILE_DIR.
Run once:
  bash $SKILL_DIR/scripts/outlook_login.sh
EOF
  exit 2
fi

if [[ ! -d "$SKILL_DIR/node_modules/playwright" ]]; then
  cat >&2 <<EOF
ERROR: Playwright not installed. Run:
  cd $SKILL_DIR && npm install && PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install chromium
EOF
  exit 1
fi

ARGS=(
  "$SKILL_DIR/scripts/fetch_emails.js"
  --hours-back  "$HOURS_BACK"
  --profile-dir "$PROFILE_DIR"
  --timeout-ms  "${FETCH_TIMEOUT_MS:-60000}"
  --max         "${FETCH_MAX:-25}"
)
[[ -n "$QUERY" ]]                    && ARGS+=( --query "$QUERY" )
[[ "${FETCH_HEADED:-0}" == "1" ]]    && ARGS+=( --headed )
[[ "${FETCH_DEBUG:-0}"  == "1" ]]    && ARGS+=( --debug )
[[ "${FETCH_ALL:-0}"    == "1" ]]    && ARGS+=( --no-filter )

# Hard-pin to the skill-local browser install; agent harnesses preset this
# var to a sandbox cache dir, which would point at a non-existent binary.
export PLAYWRIGHT_BROWSERS_PATH=0

cd "$SKILL_DIR"
exec node "${ARGS[@]}"
