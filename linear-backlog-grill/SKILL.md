---
name: linear-backlog-grill
description: Grill Linear project backlogs for execution readiness. Use when reviewing backlog quality, making Linear tickets small and clear, evaluating whether tickets are agent-executable, or turning a project's backlog into independent, well-scoped work.
---

# Linear Backlog Grill

Turn a Linear project backlog into small, independent, executable tickets. This skill is about specification quality, not whether the work is still relevant; use [backlog-hygiene](../backlog-hygiene/SKILL.md) first when the user wants stale, duplicate, or already-shipped issues removed.

A ready ticket can be handed to a zero-context executor — an engineer or coding agent that has seen none of this discussion — without follow-up questions. It has one outcome, obvious boundaries, checkable acceptance criteria, real implementation context, and explicit dependencies.

## Prerequisites

- Linear MCP available and authenticated.
- The target Linear project or team. If the user did not name one, infer it from the repo name or git remote and confirm before scanning.
- The target repo available locally when rewriting tickets — issue-writer's excerpts and commands must come from real reads of the repo, not guesses.

Stop and tell the user what's missing if Linear MCP is unavailable.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Resolve backlog
- [ ] Step 2: Collect active issues
- [ ] Step 3: Grade each ticket
- [ ] Step 4: Report the backlog map
- [ ] Step 5: Grill one ticket at a time
- [ ] Step 6: Confirm and save rewrites
```

### Step 1: Resolve backlog

Resolve the Linear project from the user's prompt, the repo name, or the git remote. Confirm the project with the user unless they named it directly.

If the user asks for a team backlog instead of a project backlog, scope to that team and say so in the report.

### Step 2: Collect active issues

Use `list_issues` filtered to the resolved project or team, paginating with `cursor` until `hasNextPage` is false. Exclude terminal issues by reading status type via `list_issue_statuses` and skipping `completed` and `canceled` statuses; never guess terminal states from display names.

For each issue, fetch enough detail to grade it:

- `get_issue` with relations when available.
- `list_comments` for prior clarification and decisions.
- Related issue links if present.

Read existing discussion before asking the user anything. Do not grill them on information already answered in comments.

### Step 3: Grade each ticket

Give every active ticket exactly one grade:

| Grade | Means | Next action |
|---|---|---|
| **Ready** | Small, clear, independent, and executable without follow-up | No rewrite needed |
| **Needs grill** | Valuable intent, but missing concrete specification | Interview and rewrite |
| **Split** | Contains multiple outcomes, phases, systems, or PRs | Break into smaller tickets |
| **Blocked** | Depends on unresolved product, design, technical, or sequencing decisions | Name the blocker before rewriting |
| **Discard candidate** | Appears irrelevant, duplicate, or already done | Hand off to [backlog-hygiene](../backlog-hygiene/SKILL.md) before closing |

Apply this bar:

- **Outcome**: one sentence says what will be true when done.
- **Reason**: user or business value is explicit.
- **Scope**: included work is specific.
- **Non-goals**: excluded work is explicit.
- **Acceptance**: criteria are objectively checkable.
- **Dependencies**: blockers and blocked-by relationships are named, or "None."
- **Context**: real files, systems, APIs, designs, examples, or links are named.
- **Verification**: tests, manual checks, screenshots, logs, or other proof are specified.
- **Size**: one focused PR, usually 1-4 hours of work.
- **Independence**: the ticket can ship on its own or names exactly what it depends on.

If any bar item is missing or vague, the ticket is not Ready.

### Step 4: Report the backlog map

Report before writing anything to Linear:

```markdown
Backlog grill for <project/team> (<N> active issues scanned):

Ready (<k>)
- <Issue ID> <Title> — <brief reason>

Needs grill (<k>)
- <Issue ID> <Title> — missing <specific gaps>

Split (<k>)
- <Issue ID> <Title> — contains <separate outcomes>

Blocked (<k>)
- <Issue ID> <Title> — blocked by <decision/dependency>

Discard candidates (<k>)
- <Issue ID> <Title> — needs backlog-hygiene evidence before action
```

For each non-Ready ticket, include the smallest useful next action. Do not batch rewrite, split, close, or comment yet.

### Step 5: Grill one ticket at a time

For each ticket the user chooses to address, run the grill to completion before moving to another ticket.

Ask only about the gaps found in Step 3, in this order:

| Gap | Grill question |
|---|---|
| Outcome | "What should be true when this ticket is done?" |
| Reason | "Who benefits from this, and why does it matter now?" |
| Scope | "What exactly is included in this ticket?" |
| Non-goals | "What should this ticket explicitly not touch?" |
| Acceptance | "How will a reviewer know this is complete?" |
| Dependencies | "Does this wait on anything, or block anything else?" |
| Context | "Which files, systems, APIs, designs, or examples should the implementer use?" |
| Verification | "What tests, manual checks, or screenshots prove it works?" |
| Size | "What is the smallest shippable slice of this work?" |

Push back once on vague answers like "make it better", "works correctly", "clean up", "use best practices", or "improve performance" without a metric. If the answer is still unknown after one pushback, record it as an open question instead of inventing a detail.

When the ticket should be split, grill for the slices first. Each child ticket must have its own outcome, scope, acceptance criteria, dependencies, and verification. Do not make sibling tickets depend on shared unstated context.

### Step 6: Confirm and save rewrites

Draft rewrites with [issue-writer](../issue-writer/SKILL.md) — read that whole skill before the first draft and follow it: its hard rules (excerpts from your own reads, verified commands, no secret values), its recon step (including the commit SHA stamp), and its description template. Skip its create step — this skill owns the Linear write flow below.

Show the exact proposed Linear changes before writing:

- For **Needs grill**: updated title if needed, full rewritten description, and any label/priority/project changes.
- For **Split**: parent update plus each proposed child issue.
- For **Blocked**: comment or description update that names the blocker and owner of the decision, if known.

Only call Linear write tools after the user approves the exact text. Save one ticket or split set at a time, then add a short Linear comment explaining that the ticket was refined for execution readiness.

## Decision Table

| Situation | Action |
|---|---|
| User asks to clean stale or duplicate tickets too | Run [backlog-hygiene](../backlog-hygiene/SKILL.md) first, then grill the remaining Keep/thin-spec tickets. |
| Ticket is relevant but too vague | Grade **Needs grill** and interview the user. |
| Ticket is both vague and too large | Grade **Split** first; the split defines the missing specification. |
| Ticket cannot move until a decision is made | Grade **Blocked** and ask who owns the decision. |
| Ticket appears done, duplicate, or obsolete | Grade **Discard candidate** and require backlog-hygiene evidence before any close action. |
| User wants autonomous agent delegation | After rewriting, optionally evaluate with [cloud-agent-triage](../cloud-agent-triage/SKILL.md). |

## Anti-patterns

- Rewriting tickets by guessing missing product intent.
- Asking the whole template at once instead of grilling the next concrete gap.
- Treating a ticket as Ready when acceptance criteria are subjective.
- Creating large "umbrella" tickets when the work should be split.
- Saving changes to Linear before the user approves the exact draft.
- Closing or canceling tickets from this skill without backlog-hygiene evidence.

## Additional Resources

- Single-ticket refinement loop: [ticket-refiner/SKILL.md](../ticket-refiner/SKILL.md)
- Agent-ready issue template: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Relevance cleanup before grilling: [backlog-hygiene/SKILL.md](../backlog-hygiene/SKILL.md)
- Autonomous agent suitability after rewriting: [cloud-agent-triage/SKILL.md](../cloud-agent-triage/SKILL.md)
