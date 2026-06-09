---
name: cloud-agent-triage
description: Evaluate whether Linear tickets are suitable for autonomous Cursor cloud agents, with explicit why-yes / why-not reasoning, then triage a repo's Linear backlog (honoring blocking dependencies) and optionally hand the ready tickets off to Cursor via the Linear MCP. Use when the user asks "is this ticket good for a cloud agent", "can Cursor do this issue", "which tickets can I assign to Cursor", "triage the backlog for background agents", "find agent-ready tickets", or "delegate suitable issues to Cursor".
---

# Cloud Agent Triage

Decide which Linear tickets an autonomous **Cursor cloud agent** can ship without a human babysitting it, explain the reasoning, and (optionally) delegate the ready ones to Cursor.

This skill has **two modes** and auto-selects based on the request:

- **Single-ticket evaluation** — the user names one ticket (`LIN-123` / URL) or pastes ticket text. Produce a verdict plus *why yes*, *why not*, and concrete fixes. Works **with or without** the Linear MCP (pasted text needs no MCP).
- **Backlog triage + optional handoff** — the user asks which tickets are agent-ready or to triage the backlog. **Requires the Linear MCP.** Resolve the repo's Linear project, list candidate issues, evaluate each, respect blockers, present a ranked shortlist, then offer to delegate the ready ones to Cursor.

The skill is **read-only by default**. The only write is the handoff, and it is always gated behind explicit user confirmation.

## Prerequisites

- **Linear MCP** available (user server or plugin) — required for backlog triage and handoff. Single-ticket evaluation on pasted text works without it.
- For handoff: the **Cursor-Linear integration** must already be connected in the workspace, on a paid Cursor plan, with the repo reachable by cloud agents. See [REFERENCE.md](REFERENCE.md#cursor-linear-handoff).

If the Linear MCP is missing, say so and fall back to single-ticket evaluation on pasted text. Stop and tell the user if a required MCP call fails with an auth error.

## Suitability rubric

Score every ticket against these dimensions. A ticket earns the **Ready** suitability verdict only when **every** dimension passes with no unresolved red flags — scope, clarity, codebase grounding, verifiability, risk, and environment self-containment. An open `blocked by` relation is handled separately by the [Blocked overlay](#verdict-mapping): a ticket that otherwise qualifies but has an open blocker is Blocked, not handoff-ready. Full rubric with examples in [REFERENCE.md](REFERENCE.md#suitability-rubric).

| Dimension | Good fit | Red flags |
|-----------|----------|-----------|
| **Scope & size** | One atomic concern, ~1-4 focused hours | "Refactor X", "improve", epics, multiple unrelated changes |
| **Clarity & acceptance criteria** | Explicit, testable definition of done | Vague/subjective goals ("make it faster" with no target) |
| **Codebase grounding** | Names real files/areas/patterns, or easily discoverable | "Somewhere in the app", no anchors |
| **Verifiability** | Validatable in an isolated VM via build/lint/tests; existing coverage is a strong plus | No way to prove it works without manual QA |
| **Risk / blast radius** | Localized, reversible | Auth, security, payments, secrets, DB migration, infra, prod data |
| **Environment self-containment** | Single repo, builds in a clean Ubuntu VM, GitHub/GitLab | Multi-repo coupling, special local state, Bitbucket |
| **Readiness prerequisites** | All inputs exist; no pending decision or manual step | A missing upstream design decision, un-provisioned credential, or other prerequisite not tracked as a `blocked by` relation (tracked blockers are handled by the Blocked overlay) |

### Verdict mapping

Give each ticket one **suitability verdict** from the rubric, then apply the **Blocked** overlay from dependencies.

Suitability verdicts (pick one):

- **Ready** — all rubric dimensions pass (no unresolved red flags, including codebase grounding and environment self-containment). Eligible for handoff once confirmed unblocked.
- **Needs refinement** — promising but missing acceptance criteria / file grounding, or too big. Suggest concrete edits first (optionally hand to [issue-writer/SKILL.md](../issue-writer/SKILL.md) to rewrite or split), then re-evaluate.
- **Not a fit** — inherently ambiguous, exploratory, or high-risk. Keep human-led.

**Blocked** is an overlay, not a fourth verdict: **any** candidate with an open `blocked by` relation is flagged Blocked **regardless of its suitability verdict**, grouped under Blocked in the proposal (noting both its underlying verdict and the blocking issue), and never eligible for handoff until the blocker resolves. Only a ticket whose suitability verdict is Ready **and** which is not Blocked counts as handoff-ready.

## Mode A: Single-ticket evaluation

1. Get the ticket: if the user named an id/URL and the **Linear MCP is available**, fetch it with `get_issue` (`id`, `includeRelations: true`) to read description, state, assignee, and `blocked by` relations. If they pasted text, use that directly — no MCP needed.
2. Score against the [rubric](#suitability-rubric).
3. Output in this format:

```
Verdict: <Ready for Cursor | Needs refinement | Not a fit | Blocked>  (LIN-123 — <title>)

Why yes:
- <dimension-grounded reason>

Why not:
- <dimension-grounded reason or gap>

To make it agent-ready:
- <specific, concrete edit — file paths, acceptance criteria, scope cut>
```

For **Ready** tickets, omit "To make it agent-ready" or replace it with a one-line handoff suggestion. For **Blocked**, name the blocking issue(s).

## Mode B: Backlog triage + optional handoff

Copy this checklist and track progress:

```
- [ ] Step 1: Confirm Linear MCP, resolve repo -> Linear project/team
- [ ] Step 2: List candidate issues (backlog/unstarted, unassigned)
- [ ] Step 3: Resolve blocking dependencies
- [ ] Step 4: Evaluate each against the rubric
- [ ] Step 5: Present ranked, grouped proposal
- [ ] Step 6: Offer handoff to Cursor (confirmation-gated)
```

### Step 1: Resolve the project

Infer the repo's Linear project from the git remote or folder name (as [issue-writer/SKILL.md](../issue-writer/SKILL.md) does), then **confirm with the user** before scanning. Allow an explicit override (project or team name). Use `list_projects` / `list_teams` to resolve names to the canonical project/team.

### Step 2: List candidate issues

`list_issues` `state` takes a **single** value, so make **one call per actionable state type** — once for `backlog` and once for `unstarted` (the `state` arg accepts a type, name, or ID; prefer the **type** so the filter works across teams without per-team lookup). For each call, filter to the resolved `project` (and/or `team`) with `assignee: null` (unassigned), read `priority`, and paginate with `cursor` until `hasNextPage` is false. **Merge both result sets and dedupe by issue id.** Only resolve concrete per-team state names/IDs via `list_issue_statuses` if you need them.

Skip issues already assigned/delegated to Cursor or to a human in progress unless the user asks to include them.

### Step 3: Resolve blocking dependencies

For each candidate, call `get_issue` with `includeRelations: true` and read its `blocked by` relations. A blocker only counts if it is **still open** — a blocker is resolved when its status **type** (`statusType`) is `completed` or `canceled`, **not** when its display name happens to read "Done". Read `statusType` directly off the blocker; map a status name to its type with `list_issue_statuses` only when the type isn't already available. Mark any candidate with an open blocker as **Blocked** (record which issue blocks it). Fetch in parallel when there are many candidates.

### Step 4: Evaluate

Give each candidate one suitability verdict from the [rubric](#suitability-rubric), then apply the Blocked overlay: any candidate with an open blocker keeps its underlying verdict but is grouped under Blocked and excluded from handoff (see [Verdict mapping](#verdict-mapping)).

### Step 5: Present the proposal

Group and rank (by priority, then strength of fit):

```
Cloud-agent triage for <project> (<N> candidates):

Ready for Cursor (<k>):
| Issue | Title | Priority | Why it fits |
|-------|-------|----------|-------------|
| LIN-101 | ... | High | small, tested, clear AC |

Needs refinement (<k>):
| Issue | Title | What's missing |
|-------|-------|----------------|

Not a fit (<k>):
| Issue | Title | Reason |
|-------|-------|--------|

Blocked (<k>):
| Issue | Title | Blocked by |
|-------|-------|------------|
```

### Step 6: Offer handoff

Only the **Ready** group is eligible. If the user wants to delegate (and the Linear MCP is available), follow [Handoff to Cursor](#handoff-to-cursor). Never auto-handoff — always confirm first.

## Handoff to Cursor

Assigning or delegating a Linear issue to **Cursor** launches a cloud agent that creates a branch, drafts a PR, and posts status back to the issue. Mechanics and setup in [REFERENCE.md](REFERENCE.md#cursor-linear-handoff).

1. **Confirm the set.** Use `AskQuestion` to let the user pick exactly which Ready tickets to hand off (allow multiple). Do not write anything before this confirmation.
2. **Resolve Cursor once.** Call `list_users` (or `get_user`) to find the workspace's Cursor agent/user and its exact name.
3. **Delegate.** Use the exact Cursor agent name/id resolved in step 2 — never hardcode the literal `"Cursor"`. For each chosen ticket call `save_issue` with `id` and `delegate: <resolved Cursor agent>` (Linear's agent-native path keeps a human owner). If the workspace exposes Cursor only as a plain user, fall back to `assignee: <resolved Cursor user>`.
4. **Verify.** Read each issue back (`get_issue`) to confirm the delegation/assignment registered.
5. **Report.** List what was handed off with issue links, and note any that failed so the user can retry.

## Decision table

| Situation | Action |
|-----------|--------|
| Linear MCP unavailable | Run single-ticket evaluation on pasted text; explain backlog scan + handoff need the MCP. |
| User pastes ticket text instead of an id | Evaluate the text directly; skip `get_issue`. |
| Repo maps to no obvious Linear project | Ask the user to name the project/team before scanning. |
| Candidate is Ready but `blocked by` an open issue | Group under Blocked; exclude from handoff; name the blocker. |
| Blocker's status type is completed/canceled | Do not treat as blocking — check `statusType`, not the display name. |
| Ticket is borderline (Needs refinement) | Suggest concrete edits or hand to issue-writer; re-evaluate after rewrite. |
| User says "assign all ready ones" | Still surface the list and confirm via AskQuestion before any `save_issue`. |
| Workspace has no "Cursor" agent user | Stop before writing; tell the user to connect the Cursor-Linear integration. |

## Anti-patterns

- Handing off **Blocked** tickets — a cloud agent can't satisfy an unfinished prerequisite.
- Calling `save_issue` (the only write) without explicit, per-ticket user confirmation.
- Marking a ticket Ready on vibes — every Ready verdict must cite the rubric dimensions it passes.
- Judging a blocker by its status display name instead of its `statusType` (`completed`/`canceled`).
- Recommending high-risk work (auth, secrets, DB migrations, infra, prod data) for autonomous execution.
- Inventing a "Cursor" assignee name instead of resolving it via `list_users`.
- Skipping `list_issues` pagination when `hasNextPage` is true — candidates get missed.

## Examples

**Single ticket, Ready:**

> Verdict: Ready for Cursor (LIN-241 — Add email format validation to signup form)
> Why yes: one atomic change; names `signup-form.tsx`; acceptance criteria are testable; existing form tests cover the area; low risk.
> Handoff: eligible — delegate to Cursor when you're ready.

**Single ticket, Not a fit:**

> Verdict: Not a fit (LIN-198 — Investigate why checkout feels slow)
> Why not: exploratory, no acceptance criteria, no target metric, touches payment path (high risk).
> To make it agent-ready: split into a measured task ("reduce `/checkout` p95 from 1.8s to <500ms") with a named hotspot file, and keep the investigation human-led.

**Backlog triage:**

> Cloud-agent triage for ButtconRAG (12 candidates): 4 Ready, 3 Needs refinement, 3 Not a fit, 2 Blocked. Want me to delegate the 4 Ready tickets to Cursor?

## Additional resources

- Full rubric, examples, handoff mechanics, and cloud-agent constraints: [REFERENCE.md](REFERENCE.md)
- Rewriting/splitting borderline tickets: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
