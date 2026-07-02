---
name: ticket-refiner
description: Interview the person who knows why a Linear ticket exists, then rewrite its description to pass issue-writer's agent-ready bar — used standalone on one ticket, or as the rewrite step from backlog-hygiene's thin-spec flag or cloud-agent-triage's Needs-refinement verdict.
disable-model-invocation: true
---

# Ticket Refiner

A vague ticket isn't fixed by an agent guessing at intent — it's fixed by asking the human who has it in their head. This skill grills that human, one gap at a time, then writes the answer into [issue-writer](../issue-writer/SKILL.md)'s description template. Read issue-writer first; this skill produces its template, not a new one.

## Prerequisites

- Linear MCP available, authenticated for the workspace.
- The issue id/identifier to refine (ask for it if not given).

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Load the ticket
- [ ] Step 2: Find the gaps
- [ ] Step 3: Interview
- [ ] Step 4: Draft
- [ ] Step 5: Confirm and save
```

### Step 1: Load the ticket

`get_issue` (`id`, `includeRelations: true`) plus `list_comments` (`issueId`). Read prior discussion before asking anything — never re-ask what a comment thread already answered.

### Step 2: Find the gaps

Map the current description against issue-writer's template sections. Mark each:

| Section | Present-and-concrete | Present-but-vague | Missing |
|---|---|---|---|
| Summary | states the change and why | states only one of the two, or restates the title | absent |
| Technical Context | real file paths and named patterns | says "relevant code" with no paths | absent |
| Requirements | specific, testable items | "improve X" with no target | absent |
| Acceptance Criteria | objectively checkable | "works correctly" | absent |
| Out of Scope | explicit exclusions | absent or "TBD" |
| Dependencies | named issues or "None" | absent |

Only **present-but-vague** and **missing** sections drive Step 3 — skip interviewing sections that are already concrete.

### Step 3: Interview

Ask about one gap at a time, not the whole template at once. Stop on a section the moment the answer would pass issue-writer's "before submitting" checklist; push back once on anything still vague before moving on:

| Gap | Ask |
|---|---|
| Summary | "What problem does this solve, and for whom?" |
| Requirements | "What's the smallest version of this that's still shippable on its own?" |
| Acceptance Criteria | "How would you verify this is done — what would a reviewer check?" (reject "works well"/"is fast" — ask for the metric) |
| Technical Context | Ask which files/patterns apply; if the human isn't sure, search the repo together rather than inventing a path |
| Out of Scope | "What's explicitly *not* included here?" |
| Dependencies | "Does this wait on anything, or block anything else?" |

If the human doesn't know an answer (genuinely undecided, not just unasked), record that explicitly in the draft rather than inventing one — an honest "Open question: X" is more agent-ready than a confident guess.

### Step 4: Draft

Fill issue-writer's [description template](../issue-writer/SKILL.md#description-template) from the interview answers plus the sections that were already concrete in Step 2. Use "None" only for sections the human confirmed don't apply — never leave a section out.

### Step 5: Confirm and save

Show the full draft to the user before writing anything. On approval:

1. `save_issue` (`id`, `description: <draft>`, plus any `project`/`priority`/`labels` that surfaced as missing or wrong during the interview).
2. `save_comment` (`issueId`, summarizing what changed and why) — an audit trail for whoever finds the ticket later.

Never call `save_issue` before the user has approved the exact draft text; re-show it if they ask for edits.

## Decision table

| Situation | Action |
|---|---|
| Every section is already concrete | Say so; skip the interview and Step 4 — nothing to refine. |
| Human gives a vague answer twice on the same gap | Record it as an open question in the draft rather than pushing a third time. |
| Refining a ticket handed off from backlog-hygiene or cloud-agent-triage | Skip re-deriving context already in that report — start the interview from its specific gap list. |
| User wants to refine multiple tickets in one session | Run Steps 1–5 fully for one ticket before starting the next — don't interleave interviews. |

## Anti-patterns

- Dumping every template section as questions at once instead of targeting only the gaps from Step 2.
- Accepting "works correctly" / "improve performance" without a concrete metric.
- Writing a file path or pattern the human didn't confirm.
- Calling `save_issue` without showing the draft first, or after only a verbal "sounds good" to a paraphrase rather than the actual text.

## Additional resources

- Description template and the agent-ready bar it must pass: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Finding tickets that need this: [backlog-hygiene/SKILL.md](../backlog-hygiene/SKILL.md) (thin-spec flag), [cloud-agent-triage/SKILL.md](../cloud-agent-triage/SKILL.md) (Needs-refinement verdict)
