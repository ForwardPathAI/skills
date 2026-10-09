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

Read [issue-writer](../issue-writer/SKILL.md) as a reference and grade against its scoping rules and quality bar. This is assessment only; do not execute a create or update workflow while grading. Record the specific failed criteria for each non-Ready issue so ticket-refiner can start from those gaps.

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

### Step 5: Refine one selected ticket

For each ticket the user chooses, read and follow [ticket-refiner](../ticket-refiner/SKILL.md) in `draft` mode. Pass the issue ID, current issue and comments, Step 3 gap list, repository evidence, and any known split boundaries or blockers.

That skill owns the interview and calls issue-writer to produce the proposed rewrite. Reuse its returned payload, readiness verdict, open questions, and change summary. Do not repeat its questions or run a separate drafting procedure. Complete the next step for this ticket or split set before starting another.

### Step 6: Confirm and save rewrites

Show the exact proposed fields and descriptions returned by ticket-refiner, including each standalone replacement and grouping document for a split. If the result is `unchanged`, report that and skip all writes.

After the user approves the exact changes:

- For a rewrite, call [issue-writer](../issue-writer/SKILL.md) in `update` mode with the source issue ID and approved payload.
- For a split, call issue-writer in `create` mode for the approved standalone issues and grouping document, then `update` mode for the source issue's agreed disposition and replacement links. Preserve the source issue; do not create sub-issues or close it unless requested.
- For a blocker that remains unresolved, save only the explicitly approved blocker note or description change. Do not label the issue Ready.

Pass the approval through to issue-writer. It owns issue writes; do not repeat them here. Record returned IDs/URLs for partial retries. After success, add one short refinement comment to the source issue, checking for an existing matching comment on a retry. This skill owns that comment because ticket-refiner ran in draft mode.

Complete when the approved changes are saved once and reported with URLs, or a specific failure is reported with the already-saved IDs.

## Decision Table

| Situation | Action |
|---|---|
| User asks to clean stale or duplicate tickets too | Run [backlog-hygiene](../backlog-hygiene/SKILL.md) first, then grill the remaining Keep/thin-spec tickets. |
| Ticket is relevant but too vague | Grade **Needs grill** and interview the user. |
| Ticket is both vague and too large | Grade **Split** first; the split defines the missing specification. |
| Ticket cannot move until a decision is made | Grade **Blocked** and ask who owns the decision. |
| Ticket appears done, duplicate, or obsolete | Grade **Discard candidate** and require backlog-hygiene evidence before any close action. |

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
