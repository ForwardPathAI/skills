---
name: standup-report
description: Generates a narratable daily standup report (yesterday / today / blockers) for yourself or a named teammate from Linear assigned issues, GitHub merged and open PRs, and local Cursor chat transcripts. Use when the user asks for a standup, daily standup, standup report, what they did yesterday, prep my standup, yesterday/today report, or a standup for a named user.
---

# Standup Report

Build a short, speakable standup script: what the target user did **yesterday**, what they plan **today**, and any **blockers**. Output is chat-only (narratable prose + optional appendix table of links).

## Scope (fixed defaults)

| Dimension | Value |
|-----------|--------|
| **Target user** | `"me"` (default) or a named Linear user (name/email) |
| **"Yesterday" window** | Previous working day — Mon → Fri; Tue–Fri → prior calendar day. On Monday, also mention Sat/Sun activity **only if any exists**. If the strict previous working day has no activity, report the last day that does. |
| **GitHub org** | `ForwardPathAI` (overridable) |
| **Transcripts** | Local user only — skip for other users and note it |
| **Output** | Narratable chat report; do not write a file or post to Notion/Linear unless the user explicitly asks |

Quote the window **end-inclusive** to the user (e.g. "covering Fri Jul 3") but compute with an **end-exclusive** ISO bound internally.

## Prerequisites

- Linear MCP authenticated for the ForwardPath workspace. Stop and tell the user to connect Linear if MCP calls fail with auth errors.
- `gh auth status` OK with access to the target org.
- `jq` and `python3` on PATH; `git` for the `git config user.email` join key (optional but recommended for the local user).
- Stop and tell the user what is missing if any prerequisite fails.

## Workflow

```
- [ ] Step 1: Resolve target user, GitHub org, and date window (absolute ISO)
- [ ] Step 2: Pull Linear issues (assigned) and current cycles; classify done/in-progress/planned
- [ ] Step 3: Pull GitHub PRs (merged-in-window, opened-in-window, still-open)
- [ ] Step 4: (local user only) Scan Cursor transcripts in the window for untracked work
- [ ] Step 5: Dedup PR ↔ issue ↔ transcript; assemble Yesterday / Today / Blockers
- [ ] Step 6: Emit the narratable report + appendix table
```

Run Steps 2, 3, and 4 in parallel.

State the resolved target user, org, and window in one line before fetching data.

### Step 1: Resolve inputs

**Target user (identity resolution)**

`me`/`@me` are authoritative — they resolve the authenticated account, so for yourself they are strictly more reliable than inferring identity from recent commits (a shared repo contains teammates' commits) or transcripts (which carry no author field). Resolve all three identities once and tie them together by **email** (the cross-system join key):

- **Linear**: `get_user` with `{ "query": "me" }` → record `id`, `email`, `displayName`, `teams: [{id, name, key}]`. `displayName` is the name used in the report header.
- **GitHub**: use `--author=@me` for queries; resolve the concrete identity for display with `gh api user --jq '{login, name, email}'` (note: `email` is often `null` when private).
- **Join key**: `git config user.email` — links the Linear email to git commits and lets you attribute local transcripts/commits to yourself.
- State the resolved identity in one line before fetching, e.g. `Pablo Schaffner · Linear pablo.schaffner@forwardpath.ai · GitHub pablo-forwardpath`. If the Linear email/name and the GitHub name/login look like **different people**, flag it and confirm with the user before continuing (the two `me`s could be authed to different accounts).

**Named user (not yourself):**

- **Linear**: `get_user` with their name or email; if not found, `list_users` with `{ "query": "<name>" }` → `displayName`, `email`, `teams`.
- **GitHub login**: derive it, don't guess blindly — match their Linear name/email against org members (`gh api orgs/<ORG>/members --jq '.[].login'`, then `gh api users/<login> --jq '{login,name}'`) or against `--author` on recent org PRs. Ask the user once only if no confident match; if still unknown, skip GitHub and note it in the report.
- **Transcripts**: skipped (local-only; see Step 4).

**Date window**

Compute from today's date (never hardcode):

| Today | Window start (inclusive) | Window end (exclusive) |
|-------|--------------------------|------------------------|
| Monday | Previous Friday | Today 00:00 local |
| Tue–Fri | Previous calendar day | Today 00:00 local |

Set `START` and `END` as `YYYY-MM-DD` for `gh search prs` date ranges. Set `END_EXCLUSIVE` as ISO datetime for `find -newermt`.

On Monday, if Sat/Sun had activity (PRs merged, issues completed, or transcripts), mention those dates explicitly in the header.

**Org**

Default `ForwardPathAI`. Use the user-named org when provided.

### Step 2: Linear issues

For the target user, fetch assigned issues in two passes (paginate `list_issues` with `cursor` while `hasNextPage`):

1. **Recently updated** — `{ "assignee": "<me or user>", "orderBy": "updatedAt", "updatedAt": "-P7D", "limit": 50 }` (wider fetch; filter in-memory to the window).
2. **Today's plan** — `{ "assignee": "<me or user>", "state": "started", "limit": 50 }` plus `{ "assignee": "<me or user>", "state": "unstarted", "limit": 50 }`.

For each team on the user record, call `list_cycles` with `{ "teamId": "<team.id>", "type": "current" }` and record current cycle `id`s.

**Classification** (in-memory; do not trust bare `updatedAt` as "work done"):

| Bucket | Rule |
|--------|------|
| **Done yesterday** | `statusType == "completed"` AND `completedAt` within `[START, END_EXCLUSIVE)` |
| **In progress yesterday** | `statusType == "started"` AND (`startedAt` in window OR issue appears in merged/opened PRs in window) |
| **Today plan** | Assigned issues with `statusType in ("started", "unstarted")`, sorted current-cycle-first (`cycleId == currentCycleId`) then priority (Urgent > High > Medium > Low > None) |

Useful issue fields: `id` (e.g. `POD2-68`), `title`, `priority.name`, `url`, `gitBranchName`, `completedAt`, `startedAt`, `status`, `statusType`, `labels`, `team`, `cycleId`.

### Step 3: GitHub PRs

Scope with `--owner=<ORG>` (a flag). Do **not** use `org:<ORG>` as a flag. Always set `--limit 100` (default is 30).

```bash
ORG=ForwardPathAI
START=2026-07-03   # replace with computed window
END=2026-07-04     # end-exclusive date for gh ranges

# Merged during the window
gh search prs --author=@me --merged --owner="$ORG" \
  --merged-at "$START".."$END" --limit 100 \
  --json number,title,repository,url,closedAt,state,body

# Opened during the window
gh search prs --author=@me --owner="$ORG" \
  --created "$START".."$END" --limit 100 \
  --json number,title,repository,url,createdAt,state,isDraft,body

# Still open (in flight / awaiting review)
gh search prs --author=@me --state=open --owner="$ORG" --limit 100 \
  --json number,title,repository,url,isDraft,createdAt
```

`gh search prs --json` does not return `headRefName` or `mergedAt`. For merged PRs, `state` is `"merged"` and `closedAt` is the merge time. Repo name is `repository.name`.

For a named user, replace `--author=@me` with `--author=<github-login>`.

### Step 4: Cursor transcripts (local user only)

Skip entirely when the target is not the machine's own user. Note in the report: "Transcripts skipped (not local user)."

Transcripts live at `~/.cursor/projects/<PROJECT-SLUG>/agent-transcripts/<uuid>/<uuid>.jsonl`. Exclude subagent files.

```bash
find ~/.cursor/projects -path '*/agent-transcripts/*/*.jsonl' \
  ! -path '*/subagents/*' -newermt "$START" ! -newermt "$END_EXCLUSIVE"
```

JSONL lines have **no per-message timestamps** — window by file mtime only. Extract real user requests from `<user_query>...</user_query>` tags (first turns include injected skill/context noise):

```bash
for f in $(find ~/.cursor/projects -path '*/agent-transcripts/*/*.jsonl' \
  ! -path '*/subagents/*' -newermt "$START" ! -newermt "$END_EXCLUSIVE"); do
  slug=$(echo "$f" | sed -E 's#.*/projects/([^/]+)/agent-transcripts/.*#\1#')
  jq -r 'select(.role=="user") | .message.content[]? | select(.type=="text") | .text' "$f" \
  | python3 -c "import sys,re; qs=re.findall(r'<user_query>(.*?)</user_query>', sys.stdin.read(), re.S); print('\n'.join(dict.fromkeys(q.strip() for q in qs)))" \
  | sed "s#^#[$slug] #"
done
```

Map slug to repo (e.g. `Users-pabloschaffner-Documents-code-forwardpath-SentrexHub` → `SentrexHub`). Caveat: multi-day sessions are attributed to their last-active day (mtime).

Drop transcript topics that clearly map to an already-listed Linear issue or PR. Surface only orphan/untracked work under **Untracked**.

### Step 5: Dedup and blockers

**PR ↔ Linear dedup**

Match Linear issue identifiers against each PR's `title` and `body` with regex `\b[A-Z]{2,}-[0-9]+\b` (case-insensitive). Also check `gitBranchName` (e.g. `pod2-68-...`). On match, collapse into one line: `Shipped POD2-68 (PR #NN in <repo>): <title>`.

If branch match is required, fall back sparingly:

```bash
gh pr view <number> --repo "$ORG/<repo>" --json number,title,headRefName,mergedAt,body
```

**Blockers** (do not invent — if none, print "Blockers: none."):

1. Open non-draft PRs awaiting review: from Step 3 open query, `state == "open"` and `isDraft == false`.
2. Started Linear issues whose `status` name or any `labels` entry matches `/block/i`.
3. Optional (small N only): `get_issue` with `{ "id": "<issue>", "includeRelations": true }` and report any `blocked by` relation.

### Step 6: Report

Use this template:

```
Standup — <displayName>, <today long date> (covering <window long date(s)>)

Yesterday:
- Shipped POD2-68 (PR #344 in SentrexHub): <one clause on what changed>.
- Progressed POD2-1971: <what advanced>; PR #349 merged.
- Untracked: <transcript work not tied to a ticket/PR> [<repo>].

Today:
- Continue POD2-1957 (current cycle, High).
- Start <next unstarted issue by priority>.

Blockers:
- PR #338 (SentrexHub) awaiting review.
```

Keep each bullet to one speakable sentence. Prefer issue ids and PR numbers over long titles.

If the user asks for detail, append a compact table:

| Item | Type | State | Link |
|------|------|-------|------|

Use Linear `url` and PR `url`.

If the window has no activity anywhere, say so explicitly under Yesterday and still list Today from assigned started/unstarted issues.

## Decision table

| Situation | Action |
|-----------|--------|
| User runs on Monday | Window = previous Friday; mention Sat/Sun only if activity exists |
| Strict previous working day is empty | Report the last day with any Linear/PR/transcript activity |
| Named user, no GitHub login | Ask once; if still unknown, skip GitHub and note it |
| Named user (not local) | Skip transcripts; note it |
| User overrides org | Replace `ForwardPathAI` in all `gh` commands |
| User wants "since last standup" or calendar yesterday | Recalculate window per their phrase; state the new bounds |
| User wants file/Notion output | Offer to do it; do not auto-write or post |
| Empty yesterday, assigned issues exist | Yesterday: "No tracked activity."; Today still populated |

## Anti-patterns

- Reporting a bare Linear `updatedAt` bump as work done — require `completedAt`/`startedAt` in window or PR evidence.
- Double-counting a PR and its linked Linear issue — dedup with identifier regex.
- Inventing "today" items not backed by assigned started/unstarted issues.
- Using `org:<ORG>` as a `gh search prs` flag — use `--owner=<ORG>`.
- Scanning `agent-transcripts/*.jsonl` (flat glob) — path is nested `*/*.jsonl`; exclude `subagents/`.
- Treating transcript file mtime as exact per-message time.
- Leaving `--limit` at the default 30 on `gh search prs`.
- Reading another user's Cursor transcripts — local-only.
- Identifying yourself from recent git commits or transcripts — a shared repo has teammates' commits and transcripts carry no author; the authenticated `me`/`@me` plus `git config user.email` (join key) are the reliable signals.

## Example output

```
Standup — Pablo, Tue Jul 7 (covering Mon Jul 6)

Yesterday:
- Shipped POD2-68 (PR #344 in SentrexHub): fixed Teams plugin language default and selection.
- Shipped POD2-1971 (PR #349 in SentrexHub): Scout percentile buckets instead of raw score.
- Untracked: adapted mobile-ui skill for skills.sh repo [skills].

Today:
- Continue POD2-1957 (current cycle, High): zero-downtime nonprod deploys.
- Start next unstarted issue in cycle by priority.

Blockers:
- PR #338 (SentrexHub) awaiting review.

| Item | Type | State | Link |
|------|------|-------|------|
| POD2-68 | Linear | Done | https://linear.app/... |
| #349 SentrexHub | PR | merged | https://github.com/... |
```
