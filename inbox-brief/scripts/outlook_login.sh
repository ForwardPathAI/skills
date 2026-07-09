#!/usr/bin/env bash
# Open a headed Chromium window under this skill's persistent profile so the
# user can log in to Outlook Web once. Subsequent headless runs of
# fetch_emails.js reuse the cookies stored in that profile.
#
# Usage:
#   bash scripts/outlook_login.sh
#
# Behavior:
#   - Creates .browser-profile/ if it doesn't exist.
#   - Launches a visible Chromium pointed at https://outlook.office.com/mail/.
#   - Closes when the user closes the window; the profile stays.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROFILE_DIR="$SKILL_DIR/.browser-profile"

if [[ ! -d "$SKILL_DIR/node_modules/playwright" ]]; then
  echo "ERROR: playwright not installed. Run:" >&2
  echo "  cd $SKILL_DIR && npm install" >&2
  echo "  PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install chromium" >&2
  exit 1
fi

mkdir -p "$PROFILE_DIR"

cat >&2 <<EOF
Opening a browser window for one-time Outlook login.
  Profile:  $PROFILE_DIR
  Target:   https://outlook.office.com/mail/
When you can see your inbox, you're done — just close the window.
EOF

# Hard-pin to the skill-local browser install; agent harnesses preset this
# var to a sandbox cache dir, which would point at a non-existent binary.
export PLAYWRIGHT_BROWSERS_PATH=0
cd "$SKILL_DIR"

node - "$PROFILE_DIR" <<'JS'
const { chromium } = require('playwright');
const profileDir = process.argv[2];

function waitUntilDone(ctx) {
  return new Promise((resolve) => {
    let done = false;
    const finish = (why) => {
      if (done) return;
      done = true;
      console.error(`[outlook-login] ${why}. profile saved.`);
      resolve();
    };
    ctx.on('close', () => finish('context closed'));
    ctx.browser()?.on('disconnected', () => finish('browser disconnected'));
    const tick = setInterval(() => {
      try {
        if (ctx.pages().length === 0) {
          clearInterval(tick);
          finish('all windows closed');
        }
      } catch (_) {
        clearInterval(tick);
        finish('context unreachable');
      }
    }, 750);
  });
}

(async () => {
  const ctx = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 1440, height: 900 },
    args: ['--disable-blink-features=AutomationControlled'],
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto('https://outlook.office.com/mail/', { waitUntil: 'domcontentloaded' });
  console.error('[outlook-login] browser open. close the Chromium window when you finish logging in.');
  await waitUntilDone(ctx);
  try { await ctx.close(); } catch (_) { /* already closed */ }
  process.exit(0);
})();
JS

echo "Login profile is ready. You can now run the skill's fetch step headless." >&2
