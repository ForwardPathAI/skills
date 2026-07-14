---
name: project-update-writer
description: Summarize everything shipped in a Linear project since its last status update and post a new project update (with health) after the user confirms. Gathers the baseline from the latest status update, lists issues completed since, groups them by capability area, and drafts a narratable update. Use when the user asks to create/write/post a project update, summarize progress since the last update, or produce a status update for a Linear project.
---

# Project Update Writer

For a named Linear project, write a new **project status update** that summarizes everything shipped **since the last update**, then post it via the Linear MCP once the user confirms. Pairs with `engineering-projects-on-track` (that skill *reads* health across projects; this one *writes* the update for one).

The update is a **write**. Draft in chat first; post only after the user confirms the body and health.

## Scope (fixed defaults)

| Dimension | Value |
|-----------|-------|
| **Target project** | Named by the user (name, slug, or URL) or inferred from context; always resolve to the project `id` + `name` before other calls |
| **Baseline** | The project's latest existing status update (`createdAt` = window start). If none exists, fall back to project start and say so |
| **Window** | Baseline `createdAt` (exclusive) → now |
| **Change source** | Linear issues in the project completed within the window (`completedAt`). GitHub PRs are an optional add-on, off by default |
| **Health** | Confirmed with the user (`onTrack` / `atRisk` / `offTrack`); default = carry over the previous update's health |
| **Tone** | Confirmed with the user: `internal` (keep issue IDs) or `client-facing` (drop IDs, outcome-focused). Default `internal` |
| **Closing section** | "Where things stand / next" — included by default |
| **Author** | The authenticated Linear user (the update posts as them) |
| **Output** | Draft in chat; post to Linear only after explicit confirmation. Do not write a file unless asked |

## Prerequisites

- Linear MCP authenticated for the workspace. Stop and tell the user to connect Linear if MCP calls fail with auth errors.
- Stop if the project cannot be resolved to a single `id` + `name`, or if any required MCP call fails — do not post a partial or guessed update.

## Workflow

```
- [ ] Step 1: Resolve the project to id + name; state it
- [ ] Step 2: Find the baseline (latest status update) and the window
- [ ] Step 3: List issues completed since the baseline (paginate; filter by completedAt)
- [ ] Step 4: Group completed work by capability/theme; count total
- [ ] Step 5: Confirm health, tone, and closing section with the user
- [ ] Step 6: Draft the body from the template; present it in chat (do NOT post)
- [ ] Step 7: On confirmation, post via save_status_update; return the URL
```

State the resolved project, baseline date, and window in one line before drafting.

### Step 1: Resolve the project

Call `get_project` with the user's query (name / slug / URL). Record `id`, `name`, `status.name`, `startDate`, `targetDate`, and whether it has milestones. Use the `id` for later write calls.

If the user did not name a project and it cannot be confidently inferred, ask which project.

### Step 2: Baseline (latest status update)

```json
{ "type": "project", "project": "<project id or name>", "orderBy": "createdAt", "limit": 1 }
```

Call `get_status_updates`. Use the **first** returned update (newest by `createdAt`). Record:

- `createdAt` → the **window start** (exclusive).
- previous `health` → the default health to carry over.
- a one-line gist of the previous `body` → to echo in the intro ("Since the last update, ...").

If the list is empty, use the project `startDate` (or creation) as the window start and state that this is the first update.

### Step 3: Issues completed since the baseline

```json
{ "project": "<project id or name>", "state": "Done", "orderBy": "updatedAt", "includeArchived": true, "limit": 200 }
```

Call `list_issues`; paginate with `cursor` while `hasNextPage` is true. Then **filter in-memory** to issues whose `completedAt >= baseline createdAt`. The API's `updatedAt` / `createdAt` "after" filters do **not** map to `completedAt`, so the window must be applied client-side.

Capture per issue: `identifier` (e.g. `POD2-525`), `title`, `completedAt`, `labels`, `priority`, `url`. Dedupe by `id`.

A quick parse when the result is large:

```bash
python3 - "$FILE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
issues = d.get("issues") or d.get("nodes") or []
since = "2026-06-05"  # baseline createdAt (YYYY-MM-DD)
rows = [(i.get("completedAt","")[:10], i.get("identifier") or i.get("id"), i.get("title"))
        for i in issues if (i.get("completedAt") or "") >= since]
rows.sort(reverse=True)
print(f"completed since {since}: {len(rows)}")
for c, ident, title in rows:
    print(f"{c}  {ident}  {title}")
PY
```

### Step 4: Group by capability/theme

Cluster the completed issues into a handful of capability areas the reader cares about, not a flat list. A useful default taxonomy (adapt per project):

- external integrations / sync
- data pipeline
- core engine (the product's main value: eval, generation, matching, ...)
- reliability / hardening
- conversational / search
- UX (candidate/user-facing)
- platform / health / access

Fold each area's issue IDs into that area's paragraph. Record the total shipped count.

### Step 5: Confirm decisions

Use `AskQuestion` with sensible defaults (skip any the user already specified):

- **Health** — `onTrack` (recommended if progress is strong and the project is active) / `atRisk` / `offTrack`. Note the `targetDate` if it has passed.
- **Tone** — `internal` (keep issue IDs, technical framing) / `client-facing` (drop IDs, outcome-focused).
- **Closing section** — include the "Where things stand / next" paragraph, yes/no.

### Step 6: Draft the body

Use this template (internal tone; client-facing = same structure minus issue IDs):

```markdown
## Progress since <Month D> — <one-line theme>

Since the last update ("<gist of previous update>"), <high-level what changed>. ~<N> issues shipped across <areas>.

**<Area 1>** — <what shipped, folded into prose> (POD2-aaa/bbb/ccc).

**<Area 2>** — <what shipped> (POD2-ddd/eee).

... one bold-lead paragraph per capability area ...

**Where things stand / next** — <current state, deployment status>. Focus now: <in-flight / UAT / next priorities>.
```

Guidance:
- Lead each paragraph with a **bold** area label; keep issue IDs in parentheses at the end of the clause they support.
- The intro should quantify (`~N issues shipped`) and echo the prior update's gist.
- Derive "next" from in-progress / current-cycle issues and any feedback captured in prior updates or project comments.

Present the full draft in chat. **Do not post yet.**

### Step 7: Post on confirmation

After the user approves the body + health:

```json
{ "type": "project", "project": "<project id>", "health": "<onTrack|atRisk|offTrack>", "body": "<markdown>" }
```

Call `save_status_update` (omit `id` to create). Return the update `url`.

Linear **auto-computes** the milestone/sprint completion-% diff and appends it to the update — surface it to the user, but never hand-write those percentages.

## Decision table

| Situation | Action |
|-----------|--------|
| No prior status update | Use project start as the window; state it's the first update |
| User says "since <date>" or "since the demo" | Use their window; state the bounds |
| User pre-specifies health/tone | Skip those questions; use their values |
| `targetDate` has passed | Flag it; ask whether health should reflect it and whether to bump the date (the user owns the date) |
| Project not found / ambiguous | Ask which project; do not guess |
| User wants a file or client variant instead of posting | Produce it in chat / file; do not post to Linear |
| Zero issues completed in the window | Say so; offer to summarize in-progress work or widen the window instead of posting an empty update |

## Anti-patterns

- Passing the project **slug** to `get_status_updates` — it can return an empty list. Resolve to the project `id`/`name` first via `get_project`.
- Trusting a bare `updatedAt` bump as "shipped" — require `completedAt` within the window, filtered in-memory (the API date filters don't map to `completedAt`).
- Hand-writing the sprint/milestone completion-% diff — Linear computes it from milestones; only the narrative `body` is yours.
- Posting without explicit confirmation — it is a write, authored as the signed-in user.
- Skipping `list_issues` pagination when `hasNextPage` is true, or double-counting an issue (dedupe by `id`).
- Dumping a flat list of 50+ tickets — group by capability area so the update is readable.

## Example output

```
## Progress since June 5 — Scout is now a live, end-to-end product on nonprod

Since the last update ("working on the UI and essentials"), Scout went from UI
scaffolding to a fully functional application deployed on nonprod, running on
live UKG data. ~59 issues shipped.

**Live UKG integration & sync** — OAuth client, abstract ATS connector, and
connectors for requisitions/candidates/documents/screening questions
(POD2-529/530/528/535); hourly sync with partial recovery (POD2-527/1953/1980).

**AI evaluation engine** — GPT-5.1 scoring/ranking, summaries, interview
questions, cross-reference validation (POD2-522/520/515/519/523).

... (one paragraph per capability area) ...

**Where things stand / next** — Live on nonprod with evaluation, chat, and
search working end-to-end. Focus now: UAT feedback and demo readiness.
```

Linear then auto-appends the milestone diff, e.g.:

```
Progress since Jun 5:
—  Sprint 3 · Resume Pipeline + Candidate List:  0% → 100%
—  Sprint 4 · AI Evaluation + Candidate Detail:  0% → 100%
```
