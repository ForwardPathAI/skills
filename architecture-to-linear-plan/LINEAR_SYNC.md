# Linear Sync

The protocol for creating the delivery plan in Linear via the `user-linear` MCP server. Runs **only after** the user approves `docs/delivery/DELIVERY_PLAN.md` (Step 5). Always read a tool's descriptor before calling it — argument shapes below are a guide, not a substitute for the schema.

## Entity mapping

| Plan concept | Linear entity | Tool |
|---|---|---|
| The delivery / product | **Project** (create or reuse) | `save_project` |
| A migration phase | **Project milestone** (with target date) | `save_milestone` |
| A ticket (functional or design) | **Issue** (in the project, assigned to a milestone) | `save_issue` |
| The plan overview | **Document** (project-linked) | `save_document` |
| Dependencies | Issue relations `blocks` / `blockedBy` | `save_issue` (second pass) |

Linear milestones are **project milestones**, not initiatives — the user asked for milestones, so create real ones under one project. (Use an initiative only if the delivery spans multiple projects, via `save_project` `addInitiatives`.)

## The approval gate

Do not call any `save_*` (write) tool until the user has explicitly approved the plan. The `list_*` readers are safe to call earlier (Step 6.1) to resolve targets. If approval hasn't been given, the only deliverable is `DELIVERY_PLAN.md`.

## Step 6.1 — Resolve targets (readers only)

Resolve every reference to a real workspace object before creating anything:

- `list_teams` → confirm the target **team** with the user (required for projects and issues).
- `list_projects` → does a project for this delivery already exist? If so, reuse it (idempotent update); else create.
- `list_issue_labels` / `list_project_labels` → the set of labels that exist. **Apply only existing labels.** If the plan wants a `design` / `functional` split and those labels don't exist, ask before `create_issue_label`.
- `list_cycles` → if mapping onto sprints.
- `list_users` → for `lead` / `assignee` if the user named owners; otherwise leave unassigned.
- `list_issue_statuses` → the team's initial state (usually Backlog/Triage) if you need to set `state`.

Never invent a team, project, label, or user name — resolve or ask.

## Step 6.2 — Create the project

`save_project` — `name` + at least one team (`addTeams`) are required to create. Set:

- `name`, `summary` (≤255 chars), `description` (Markdown; literal newlines, not `\n`).
- `startDate` / `targetDate` from the approved timeline; add `startDateResolution` / `targetDateResolution` (`month`/`quarter`) when dates are coarse.
- `lead` and `priority` (0=None…4=Low) if known.

If reusing an existing project, pass its `id` to update rather than duplicate.

## Step 6.3 — Create milestones

For each milestone, `save_milestone` with `project` + `name` (required) + `description` (its exit criterion) + `targetDate`. Record the returned milestone name/ID for issue assignment.

## Step 6.4 — Create issues

For each ticket, `save_issue`:

- `title` + `team` are required on create. Set `project` and `milestone` (by name or ID).
- `description` = the full issue-writer / design-ticket body as Markdown (literal newlines; **no escaped `\n`**).
- `priority` (0–4 per the descriptor), `estimate` (the plan's number; match the team's scale), `labels` (existing only).
- `links` = `[{ url, title }]` for design tickets — attach the mockup and the screen-spec/architecture reference. Do **not** attach anything containing secrets or the PAT-bearing remote URL.
- `dueDate` only if the plan pins per-ticket dates (usually milestone dates suffice).

Create all issues **first**, collecting their identifiers, before wiring relations.

## Step 6.5 — Wire dependencies (second pass)

Once every issue exists, set relations with `save_issue` (update by `id`): `blockedBy` / `blocks` (append-only) per the dependency graph from [WORK_BREAKDOWN.md](WORK_BREAKDOWN.md). Keep it acyclic. Relations can't reference issues that don't exist yet — that's why this is a separate pass.

## Step 6.6 — Grouping document

`save_document` — the plan overview mirroring [issue-writer splitting.md](../issue-writer/splitting.md)'s document convention: feature overview, the milestone → ticket table, shared technical context (the architecture summary), and feature-level "done when." Link it to the project. Add its URL to each issue's `links` (or reference it in the description) so an executor can find the whole plan from any ticket.

## Idempotency & re-runs

The skill must be safe to run twice:

- Match projects, milestones, and issues **by name** against the `list_*` results before creating. If found, `save_*` with the existing `id` to update; never create a second copy.
- Relations and `links` are append-only in the MCP — don't re-add ones already present.
- If a partial run failed midway, re-running resumes: existing entities are updated, missing ones created.

## Reporting

Report back: the project URL, the document URL, each milestone with its target date, and the issue count per milestone (with identifiers). State the `docs/delivery/DELIVERY_PLAN.md` path. Never echo secret values or the raw remote URL.
