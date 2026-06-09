# Cloud Agent Triage — Reference

Detailed rubric, handoff mechanics, and cloud-agent constraints for [SKILL.md](SKILL.md). Read this when you need the deeper "why" behind a verdict or the exact handoff setup.

## Mental model

Treat a Cursor cloud agent as a **smart but low-context developer** dropped into an isolated VM with only the issue text, the repo, and whatever the repo's `AGENTS.md` / rules / skills provide. It plans, edits files, runs shell commands, runs tests, and opens a PR — but it cannot ask clarifying questions mid-flight, cannot see your laptop's state, and will not stop itself well without a clear definition of done. **Scope creep is the named failure mode**: a vague task yields a large, hard-to-review PR that no one merges.

Suitability is therefore as much about the **environment and the ticket's specification** as about the task category.

## Suitability rubric (detailed)

### 1. Scope & size

One atomic concern, completable in roughly 1-4 focused hours, producing a small reviewable diff.

- Good: "Add email format validation to the signup form", "Add unit tests for `dateUtils`", "Bump `axios` to v1.x and fix the one breaking call".
- Bad: "Refactor the auth module", "Improve the dashboard", anything with "and" joining unrelated work.

A strong stopping condition is: tests pass **and** the diff is small enough to review **and** the change is summarizable in one paragraph.

### 2. Clarity & acceptance criteria

An explicit, testable definition of done. The agent must be able to *evaluate* whether it succeeded.

- Good: "`/users` returns 422 with a field error when email is malformed; existing tests still pass."
- Bad: "Make validation better", "Handle edge cases" (which ones?).

### 3. Codebase grounding

Real anchors — file paths, component names, the pattern/utility to follow — or a description specific enough that the agent can find them. Tickets that name a similar existing implementation are ideal.

### 4. Verifiability

The change can be proven correct inside a clean VM via build, lint, and tests. **Existing test coverage on the touched area is the single strongest positive signal** — the agent is only as reliable as the test suite it can run. If the only way to verify is manual QA or a human eyeball, it's a weaker fit.

### 5. Risk / blast radius

Low-risk, localized, reversible changes are good fits. Escalate to human-led for:

- Authentication / authorization / security-sensitive code
- Payments / billing
- Secrets handling
- Database schema migrations
- Infrastructure / deploy / prod-data changes

These are "critical risk" regardless of how well-specified they are.

### 6. Environment self-containment

- Single repo that builds in a clean Ubuntu VM with standard install/build steps.
- No dependency on special local state, undocumented env vars, or services only on the author's machine.
- GitHub or GitLab (cloud agents do not support Bitbucket).
- Secrets, if genuinely needed to build/test, must be configured in the Cursor Secrets settings — a ticket that needs ad-hoc local secrets is a poorer fit.

### 7. Dependencies / readiness

Not blocked by an unfinished issue, and free of manual prerequisites (a design decision, an API key someone must provision, an upstream merge). See [Dependency handling](#dependency-handling).

## Verdict examples

| Ticket | Verdict | Reasoning |
|--------|---------|-----------|
| "Add `aria-label` to icon buttons in `Toolbar.tsx`" | Ready | Tiny, grounded, visually verifiable, zero risk. |
| "Add tests for `parseCsv` covering empty + malformed rows" | Ready | Bounded, test-shaped, strong verifiability. |
| "Migrate users table to add `last_login` column" | Not a fit | DB migration = critical risk; human-led. |
| "Fix the flaky checkout test" | Needs refinement | No reproduction; ask for the failing test name + error first. |
| "Build the reporting feature" | Needs refinement | Epic; split into vertical slices via issue-writer. |
| "Investigate slow dashboard" | Not a fit | Exploratory, no acceptance criteria, no target. |
| "Wire the export button to the new `/export` API" (blocked by the API ticket) | Blocked | Ready in shape, but the API endpoint isn't merged yet. |

## Dependency handling

1. Read relations with `get_issue` (`includeRelations: true`) and look at `blocked by`.
2. A blocker only counts if it is **still open**. Judge by the blocker's status **type** (`statusType`): treat `completed` or `canceled` as resolved, never the display name (a custom "Done"-style name may not map to `completed`). Use `list_issue_statuses` only to map a status name to its type when the type isn't already on the issue.
3. Mark any candidate with an unresolved blocker as **Blocked** and record the blocking identifier. Blocked tickets are excluded from handoff even if otherwise Ready.
4. When a chain of issues exists, the earliest unblocked, Ready ticket is the best handoff candidate; downstream ones become eligible once their blockers close.

## Cursor-Linear handoff

### Mechanism

Cursor cloud agents are triggered **from Linear** by:

- Setting the issue **assignee** to "Cursor", or
- **Delegating** the issue to the Cursor agent (the human stays the owner; Cursor is added as a contributor), or
- An **`@Cursor` mention** in a comment (also used to send follow-up instructions to a running agent).

Once triggered, Cursor pulls in the issue details, comments, and linked references, spins up a cloud agent, **creates a branch, drafts a PR, and syncs status back to the Linear issue**. You can monitor it from Linear, the Cursor web app, or the IDE.

Note: a **label alone does not trigger an agent** — labels only configure repo/model/branch. Triage rules and Automations can auto-delegate, but Linear currently requires a human assignee for triage rules to fire.

### Doing it via the Linear MCP

This skill uses `save_issue` to perform the handoff. **Resolve the exact Cursor agent name/id first with `list_users` — do not hardcode the literal `"Cursor"`**, since the integration user may be named differently:

- Preferred: `save_issue` with `id` + `delegate: <resolved Cursor agent>` — the agent-native path; keeps a human owner.
- Fallback: `save_issue` with `id` + `assignee: <resolved Cursor user>` — when the workspace exposes Cursor only as a plain user.

After writing, read the issue back with `get_issue` to confirm the change registered.

### Setup prerequisites (tell the user if missing)

- The Cursor-Linear integration is connected for the workspace/team (installed by an admin from the Cursor dashboard).
- A paid Cursor plan (Pro/Ultra) with cloud agents enabled.
- A default repository (and base branch/model) configured in the Cursor dashboard, or a repo mapping for the project.
- The repo is reachable by cloud agents and builds in a clean environment.

If there is no "Cursor" agent/user in the workspace, stop before writing and ask the user to connect the integration.

## Cloud-agent constraints (why environment matters)

- Runs in an **isolated Ubuntu VM** — no access to the author's local machine, local services, or uncommitted local state.
- Needs the repo to **install, build, and test** from a clean checkout; missing steps cause failures the agent can't resolve.
- **Secrets** are only available if configured in Cursor's Secrets settings, not pulled from a local `.env`.
- **Single repo** by default (multi-repo is possible but a weaker default fit); cross-repo changes are a poor autonomous fit.
- **GitHub/GitLab only** (no Bitbucket).
- Bounded CPU/memory and a finite run window — very large tasks time out or drift.

These constraints are why a perfectly-worded ticket can still be a poor fit if the repo can't build cleanly in a VM or the work needs local secrets.

## Sources

- Cursor docs: Linear integration (`cursor.com/docs/integrations/linear`), "Bringing the Cursor Agent to Linear" (`cursor.com/blog/linear`).
- Linear docs: assigning and delegating issues (`linear.app/docs/assigning-issues`); Cursor background agents changelog (`linear.app/changelog/2025-08-21-cursor-agent`).
- Industry guidance on scoping autonomous coding agents (well-scoped, well-tested, low-risk, isolated-VM execution; scope creep as the primary failure mode).
