# First-time setup

This skill reads your Microsoft 365 mailbox through a persistent **Chromium
profile** driven by Playwright on Outlook Web — no Graph API tokens, no
admin consent (the ForwardPath tenant requires admin approval for any Graph
`Mail.Read` app, so the API route is closed). Outlook just sees a browser
logged in as you.

Three steps, all run from the skill directory:

```bash
cd <skill-dir>   # wherever this skill is installed
```

## 1. Prerequisites

| Tool | Why | How to get it |
|------|-----|---------------|
| Node.js ≥ 18 | Playwright runtime | `brew install node` |
| `jq` | JSON wrangling | `brew install jq` |
| Linear MCP | Issue correlation | already configured in Cursor |

## 2. Install Playwright and the browser

```bash
npm install
PLAYWRIGHT_BROWSERS_PATH=0 npx playwright install chromium
```

`PLAYWRIGHT_BROWSERS_PATH=0` keeps the ~200 MB browser binary inside
`node_modules/playwright-core/.local-browsers/` co-located with the skill.
The wrapper scripts set the same env var at runtime.

## 3. Log in to Outlook (one time)

**Shortcut — reuse an existing Microsoft browser profile.** If another
skill already keeps a logged-in Microsoft session (e.g.
`review-prs-from-teams` and its `.browser-profile/`), just copy it: the
Microsoft SSO cookies cover Outlook too, no interactive login needed.

```bash
cp -R ~/.cursor/skills/review-prs-from-teams/.browser-profile .browser-profile
```

**Otherwise, log in interactively:**

```bash
bash scripts/outlook_login.sh
```

A Chromium window opens at `https://outlook.office.com/mail/`. Sign in as
your work account (including MFA) and tick **"Stay signed in"** so the
cookie survives. When you can see your inbox, close the window. Cookies are
saved under `.browser-profile/` (gitignored).

Re-run this script (or re-copy a fresh profile) whenever a fetch fails
with `redirected to login`.

## 4. Verify

```bash
bash scripts/fetch_emails.sh 24 | jq 'length'
FETCH_HEADED=1 FETCH_DEBUG=1 bash scripts/fetch_emails.sh 24 | jq 'length'   # watch it work
```

## Troubleshooting

**`browser profile not found`** → run step 3.

**`redirected to login`** → cookie expired; re-run step 3.

**`could not find the Outlook message list`** → the channel didn't load in
time (`FETCH_TIMEOUT_MS=90000`) or Microsoft changed OWA's DOM. Run with
`FETCH_HEADED=1 FETCH_DEBUG=1`, inspect the page, and update the selector
candidates in `scripts/fetch_emails.js` (`findListbox`, `readRows`,
`extractConversation`).

**Structured `messages` come out empty** → OWA body-container selectors
drifted; `paneText` still carries the full reading-pane text, so the brief
still works. Fix selectors when convenient.

**A real email is being filtered out** → check `filters.json`; row-sender
names match the list row, email regexes match participants after opening.
Run with `FETCH_ALL=1` to bypass all filters.

**Reading emails marks them as read** → yes, opening a conversation in the
reading pane can mark it read, same as reading it yourself. There is no
read-only open in the web UI.
