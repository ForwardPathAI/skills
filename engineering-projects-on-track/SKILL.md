---
name: engineering-projects-on-track
description: Calculates the share of ForwardPath Engineering team Linear projects that are on track from the latest project status update. Filters to In Progress and UAT projects only; on track means health onTrack, everything else counts off track. Use when the user asks for projects on track, engineering project health %, on-track ratio, portfolio status, or "how many projects are on track".
---

# Engineering Projects On Track

Report what percentage of active ForwardPath Engineering projects are **on track**, using each project's **latest** Linear project status update.

## Scope (fixed defaults)

| Dimension | Value |
|-----------|--------|
| **Team** | `ForwardPath Engineering` (Linear team name; also matches user phrases like "ForwardPath AI Engineering") |
| **Project states** | `In Progress` **or** `UAT Testing` only (match `status.name` exactly; do not include Backlog, Planned, On Hold, Completed, Canceled) |
| **Health source** | Latest project status update (`get_status_updates`, `type: "project"`) |
| **On track** | `health === "onTrack"` on that update |
| **Off track** | `atRisk`, `offTrack`, or **no status update** |

`atRisk` counts as off track. Do not use project workflow state or priority as a proxy for health.

## Prerequisites

- Linear MCP (`plugin-linear-linear`) authenticated for the ForwardPath workspace.
- Stop and tell the user to connect Linear if MCP calls fail with auth errors.

## Workflow

```
- [ ] Step 1: List all ForwardPath Engineering projects (paginate)
- [ ] Step 2: Filter to In Progress + UAT Testing
- [ ] Step 3: Fetch latest status update per project
- [ ] Step 4: Classify and report
```

### Step 1: List projects

Call `list_projects` with `team: "ForwardPath Engineering"` and `limit: 50`. If `hasNextPage` is true, repeat with `cursor` until all projects are collected.

### Step 2: Filter projects

Keep projects where `status.name` is one of:

- `In Progress`
- `UAT Testing`

Record `name`, `url`, and `status.name` for the report appendix.

### Step 3: Latest status update per project

For each in-scope project, call `get_status_updates`:

```json
{
  "type": "project",
  "project": "<project name>",
  "limit": 1,
  "orderBy": "createdAt"
}
```

Use the **first** returned update (newest by `createdAt`). Read `health`:

| `health` | Counts as |
|----------|-----------|
| `onTrack` | On track |
| `atRisk` | Off track |
| `offTrack` | Off track |
| (empty list) | Off track |

Display labels for humans: **On track**, **At risk**, **Off track**, **No update**.

Fetch updates in parallel when there are many projects.

### Step 4: Calculate and report

```
on_track = projects where latest health is onTrack
total    = all In Progress + UAT Testing projects in Step 2
pct      = round(on_track / total * 100)   # whole number; if total is 0, say so and skip %
```

**Primary line (required):**

```
<pct>% (<on_track>/<total>)
```

Example: `57% (4/7)`

**Supporting detail (brief):**

- Team and state filter used
- Table of each project: name | project state | latest health | update date (`createdAt` of latest update, or "—")

Optional: link each project via its `url` from `list_projects`.

## Decision table

| Situation | Action |
|-----------|--------|
| User names a different team | Use their team; still apply the same state and health rules unless they override. |
| Workspace uses `In UAT` instead of `UAT Testing` | Include both names in the state filter if both exist; document which names were matched. |
| Project has updates but `health` is null | Treat as off track; note in the table. |
| `total` is 0 | Report "No In Progress or UAT projects on ForwardPath Engineering" — do not invent a percentage. |
| User wants only In Progress or only UAT | Narrow the state filter; recalculate. |

## Anti-patterns

- Counting Backlog, Planned, On Hold, or Completed projects in the denominator.
- Using `list_projects` health fields — health lives on **status updates**, not the project record.
- Treating `atRisk` as on track.
- Using an older status update when a newer one exists (always `limit: 1`, `orderBy: "createdAt"`).
- Skipping pagination on `list_projects` when `hasNextPage` is true.

## Example output

```
Engineering projects on track (ForwardPath Engineering · In Progress + UAT Testing):

71% (5/7)

| Project | State | Latest update |
|---------|-------|---------------|
| [ForwardPath] Portal | In Progress | On track (2026-05-26) |
| [Kinectrics] Bid Vault / DB Migration & Tool Expansion | UAT Testing | At risk (2026-05-20) |
...
```
