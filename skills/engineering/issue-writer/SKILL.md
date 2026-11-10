---
name: issue-writer
description: Write Linear issues an AI coding agent can execute without follow-up questions. Use when the user wants to create a Linear issue/ticket/bug, or turn a feature into a spec and a set of tickets.
---

# Linear Issue Writer

Every issue is a handoff to an **executor** with **zero context**: an AI coding agent (or unfamiliar developer) that has not seen this conversation or any other issue. The issue gives it a clear outcome and the judgment to reach it; the executor reads the code itself. Output goes into Linear via the Linear MCP server, not a chat reply.

An issue describes **behavior**, not files. Code moves between the day a ticket is written and the day it runs, so an issue that pins scope to paths and line numbers goes stale and stalls its executor. An issue that pins the outcome, the boundaries, and the decisions stays true while files change under it.

Three properties make an issue executable:

1. **Outcome** — one end-to-end behavior, stated from the user's or caller's view, with the reason it matters. Intent lets the executor make the right call when the code looks different than expected.
2. **Checkable acceptance** — criteria a reviewer can check: a test that passes, a response, a screen state. Never "works correctly".
3. **Boundaries** — what stays out of scope, the decisions already made, and the few ticket-specific conditions that need a human. Everything else is the executor's call.

## Hard rules

1. **Starting points come from your own reads.** Open every file or symbol you name. They are leads to where the code lives today, never a list of the only files to touch.
2. **Never reproduce secret values.** Linear is an external system. If context includes credentials, tokens, or `.env` contents, name the location and credential type only.
3. **Commands are verified, not guessed** — pulled from `package.json`, CI config, or repo docs.

## Workflow

1. **Recon** — read enough of the repo to write from evidence:
   - What changes, in which repo, and what the user is trying to accomplish.
   - Where the behavior lives today (modules, symbols) and one exemplar the executor should match.
   - The **seam** to test at: prefer an existing one, as high as possible (an API route over an internal helper).
   - Intent docs where present (`CLAUDE.md`/`AGENTS.md`, ADRs, `CONTEXT.md`, `DESIGN.md`) — carry over the decisions that constrain this work.
2. **Fetch teams, projects, and labels from Linear via MCP** — use existing workspace values; never invent names.
3. **Resolve placement without routine confirmation** — honor any team/project the user named. Otherwise infer from the repo name, git remote, existing issues, and session context. Use a clearly matching project when one exists. If none fits, create the issue under the known team without a project; do not create a project or attach unrelated work to one to fill the field. Ask only when the team is unknown or several placements remain plausible.
4. **Scope** — if the work needs more than one ticket, follow [Specs and splitting](splitting.md): it writes a spec, then tracer-bullet tickets that use the template below.
5. **Write** — follow the [Description template](#description-template).
6. **Create via Linear MCP** with all required fields set, and blocking relations set natively (`blockedBy`).

## Required fields (every issue)

| Field | Rule |
|-------|------|
| **Team** | Required. Use the team named by the user or established by repo/workspace context. |
| **Project** | Optional. Follow the placement rules above; omit it or pass `null` for a team-only issue. |
| **Priority** | Required. Urgent / High / Medium / Low. Default Medium if unspecified. |
| **Labels** | Required. Pull from Linear; apply only existing labels. |
| **Title** | Imperative mood, stating what will be true after the issue lands. "Add email validation to signup form", not "Signup issue". |
| **Description** | Required. Use the template below. |

## Description template

The top half is for people; the collapsible **Agent notes** section (Linear's `+++` block) holds what the executor needs. Fill every section. Write "None" for sections that don't apply.

```markdown
## Why
[2–4 sentences: the problem, its concrete cost, what improves when this lands.]

## What to build
[The end-to-end behavior this ticket makes work, from the user's or caller's view.
One outcome, not a layer-by-layer task list. For a bug: steps, expected vs actual, and the error.]

## Acceptance criteria
- [ ] [Observable behavior a reviewer can check]
- [ ] [A named test at the seam below passes]
- [ ] `<verified typecheck/lint command>` exits 0

## Out of scope
- [Behavior, contract, or area this ticket leaves alone — one line on why]

+++ Agent notes

**Spec:** [Linear document link, or None]

**Decisions** (made already; follow them):
- [Module, interface, contract, or schema decision this ticket depends on]

**Starting points** (where this lives today; follow the behavior if it has moved):
- [Module or symbol, with its role — e.g. `listOrders` in the orders service builds the N+1 query]
- Match: [exemplar convention, e.g. the Result-pattern error handling in the users API]

**Test seam:** [Where to test and which existing test to model after]

**Ask first if:**
- [Ticket-specific assumption that, if false, invalidates the approach — or None]

+++
```

Keep line numbers and code excerpts out: the executor reads the current code. One exception: a snippet that pins a decision more precisely than prose (a schema, a type shape, a state machine) goes under Decisions, trimmed to the decision.

## Scoping rules

Each issue is:

- **Small** — one focused PR, 1–4 hours, done in one fresh context window.
- **Independent** — lands green on its own and names only real blockers.
- **Vertical** — a thin path through every layer it needs (schema, API, UI, tests), not one layer.
- **Checkable** — pass/fail criteria are objective.

If one issue can't hold all four, split (see [Specs and splitting](splitting.md)).

## Quality bar — check before creating each issue

- Could an executor that has never seen this repo or conversation start with only the issue and the repo?
- Does "What to build" state one outcome, so the executor can judge any file change by whether it serves that outcome?
- Is every acceptance criterion checkable, with any command verified?
- Does "Out of scope" name behaviors or areas, so the boundary holds after files move?
- Are "Ask first" items specific to this ticket? The executor already stops for decisions it can't make; generic stop rules belong in [execute](../execute/SKILL.md), not here.
- Team, priority, and labels are set; project follows the placement rules; blockers are native relations.
- No secret values anywhere — locations and credential types only.
