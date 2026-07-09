---
name: inbox-brief
description: >-
  Produce a context brief of the user's Microsoft 365 (Outlook) inbox — today's
  received emails by default, or specific emails/threads the user names — by
  scraping Outlook Web through a persistent Playwright Chromium profile (no
  Graph API, no admin consent), filtering out GitHub notifications and
  automated noise, then enriching each real thread (customers, forwardpath.ai
  teammates) with related Linear issues via the Linear MCP and related local
  Cursor chat transcripts. Read-only: never sends, replies, or marks mail as
  read. Use when the user says "check my email", "inbox brief", "what came in
  today", "catch me up on my inbox", "brief me on the email from <X>", or any
  variant of gathering context around received emails.
---

# Inbox Brief

Build a per-thread context brief from the user's Outlook inbox: what each
email thread is about, who's waiting on whom, and what the related Linear
issues and past Cursor chats say. Chat-only output; read-only against the
mailbox.

## Scope (fixed defaults)

| Dimension | Value |
|-----------|-------|
| **Window** | Today (since local midnight) by default; "last N days/hours" widens it |
| **Specific emails** | If the user names a sender/topic ("the email from Acosta about the outage"), search instead of the window |
| **Noise** | GitHub notifications, automated senders, calendar responses, OOO — see `filters.json`. Junk folder never scraped (inbox only) |
| **Keep** | Threads with at least one human: a customer or a `@forwardpath.ai` teammate |
| **Enrichment** | Linear MCP issues + local Cursor transcripts. GitHub PRs only if an email explicitly references one |
| **Output** | Chat brief; never writes to the mailbox, Linear, or files unless asked |

## Prerequisites

- One-time setup complete (Playwright + Chromium in the skill dir, Outlook
  login profile saved): see [SETUP.md](SETUP.md). If the fetch script exits
  with code 2, first try copying a logged-in Microsoft profile from another
  skill (SETUP.md §3 shortcut); otherwise tell the user to run
  `bash scripts/outlook_login.sh` — do not try to log in for them.
- Linear MCP authenticated. If Linear calls fail with auth errors, produce
  the brief without Linear and say so.
- `jq`, `node` ≥ 18 on PATH.

## Workflow

```
- [ ] 1. Resolve window / search query from the user's request
- [ ] 2. Fetch emails (headless Outlook scrape)
- [ ] 3. Extract entities per thread (participants, companies, issue keys, topics)
- [ ] 4. Correlate: Linear MCP + Cursor transcripts (parallel)
- [ ] 5. Emit the brief
```

Skill directory: resolve relative to this SKILL.md file. All scripts below
are relative to that path.

### Step 1: Resolve the request

| User says | Action |
|-----------|--------|
| nothing specific / "today" | `HOURS` = hours since local midnight (min 6) |
| "last N days" / "last N hours" | `HOURS` = N×24 / N |
| "the email from X about Y" | `QUERY` = `"X Y"` distilled to 2–4 search words |
| "including github/all emails" | set `FETCH_ALL=1` |

### Step 2: Fetch emails

```bash
bash <skill-dir>/scripts/fetch_emails.sh "$HOURS" ["$QUERY"] > /tmp/inbox.json
jq length /tmp/inbox.json
```

Under the hood: headless Chromium under the skill's persistent profile
(`.browser-profile/`), scrolls the inbox list back to the cutoff (or runs
the query through Outlook search), skips noise rows per `filters.json`,
opens each remaining conversation in the reading pane, and emits JSON:
one object per conversation with `subject`, `rowSender`, `rowTimeIso`,
`participants` (email addresses), `messages` (structured author/time/body
where the DOM allows), and `paneText` (full reading-pane text — the
authoritative fallback when `messages` came out empty or mangled).

Error modes — point the user at [SETUP.md](SETUP.md), don't auto-fix:

| Error | What to do |
|---|---|
| exit 2 / `browser profile not found` | Run `bash scripts/outlook_login.sh` once. |
| exit 2 / `redirected to login` | Outlook cookie expired; re-run `outlook_login.sh`. |
| `could not find the Outlook message list` | DOM drift. Re-run with `FETCH_HEADED=1 FETCH_DEBUG=1` and update selectors in `scripts/fetch_emails.js`. |
| 0 conversations but the user expects mail | Check the window first; then re-run with `FETCH_ALL=1` to see if filters ate everything, and say which filter did. |

Cap: the script opens at most 25 conversations (`FETCH_MAX` to override).
If the window has more, brief the 25 newest and say the rest were skipped.

### Step 3: Extract entities per thread

From `messages` + `paneText` of each conversation, collect:

- **Participants**: split into teammates (`@forwardpath.ai`) and externals;
  map external domains to customer/company names.
- **Linear issue keys**: regex `\b[A-Z]{2,}-[0-9]+\b` — strong links.
- **Repo / PR references**: `github.com/<org>/<repo>` URLs, `#123` near a
  repo name.
- **Topic keywords**: 2–4 distinctive terms per thread (product names,
  feature names, error strings) — for fuzzy search. Skip generic words.
- **Asks**: who asked whom for what, and whether the last message in the
  thread is waiting on the user.

### Step 4: Correlate (run Linear and transcripts in parallel)

**Linear (MCP)**

- Every issue key found → `get_issue` (id, title, status, assignee, url).
- Per thread without keys → one `list_issues` query with the best topic
  keyword (`{ "query": "<keyword>", "orderBy": "updatedAt", "limit": 5 }`);
  keep only results whose title/description plausibly matches the thread.
  Do not force a match — "no related issues" is a fine answer.

**Cursor transcripts (local)**

Transcripts live at `~/.cursor/projects/<slug>/agent-transcripts/*/*.jsonl`
(exclude `subagents/`). Grep, don't parse:

```bash
grep -rl -i -e "<keyword1>" -e "<keyword2>" \
  ~/.cursor/projects/*/agent-transcripts --include='*.jsonl' 2>/dev/null \
  | grep -v '/subagents/'
```

For each hit, pull the user queries to identify what the chat was about:

```bash
jq -r 'select(.role=="user") | .message.content[]? | select(.type=="text") | .text' "$f" \
  | python3 -c "import sys,re; qs=re.findall(r'<user_query>(.*?)</user_query>', sys.stdin.read(), re.S); print('\n'.join(dict.fromkeys(q.strip()[:200] for q in qs)))"
```

Keep at most the 3 most relevant transcripts per thread; cite them as chat
links `[<title ≤6 words>](<uuid>)` using the jsonl filename's uuid.

**GitHub (only if referenced)**: if a thread explicitly cites a PR, fetch
its state with `gh pr view <url> --json state,title,mergedAt`.

### Step 5: The brief

```
Inbox brief — <today long date>, <window description>
<N> threads (skipped: <M> noise, <K> over cap)

1. <Subject> — <customer/company or "internal">
   From <sender> at <time> · participants: <short list>
   <2–3 sentence summary: what the thread is about and where it stands.>
   Waiting on you: <yes — what they need / no>
   Linear: POD2-123 (In Progress, assigned <who>) — <how it relates>
   Chats: [<chat title>](<uuid>) — <one clause on what was discussed>

2. ...

Needs a reply from you: <list of thread numbers, or "nothing">
```

Rules:

- Order: threads waiting on the user first, then by recency.
- "Waiting on you" only when the last message asks the user something or
  assigns an action — not merely because the user was the recipient.
- Omit the Linear/Chats lines when there's nothing related; never invent a
  connection.
- Quote deadlines, amounts, and commitments verbatim from the email.
- If the user asked about one specific email, expand that thread fully
  (message-by-message rundown) instead of the numbered digest.

## Decision table

| Situation | Action |
|-----------|--------|
| Fetch exits 2 | Tell the user to run `outlook_login.sh`; stop. |
| Linear MCP auth fails | Brief without Linear; note it. |
| 0 threads after filtering | Say so; list what was filtered (senders) so the user can spot a false positive. |
| Thread in a language other than English | Summarize in English; quote key asks in the original. |
| User asks to reply / send mail | Decline that part — the skill is read-only; offer draft text in chat instead. |
| Filters eat a real email (user complains) | Show which pattern matched; offer to edit `filters.json` for them. |

## Anti-patterns

- Marking mail as read, replying, archiving — never; the scraper only clicks
  to open the reading pane, which Outlook may mark as read as a side effect;
  warn the user about that side effect the first time in a session.
- Trusting the structured `messages` split blindly — when it's empty or
  looks truncated, fall back to `paneText`.
- Forcing a Linear/transcript match for every thread.
- Grepping transcripts with generic keywords ("meeting", "update") — use
  distinctive terms only.
- Scanning `agent-transcripts/*.jsonl` flat — the path is nested
  `*/*.jsonl`; exclude `subagents/`.
- Re-scraping for each follow-up question — reuse `/tmp/inbox.json` within
  a session unless the user asks to refresh.

## Additional resources

- First-time setup (install Playwright, log in to Outlook once): [SETUP.md](SETUP.md)
- Noise filter config: `filters.json` (row sender names, sender email
  regexes, subject regexes)
