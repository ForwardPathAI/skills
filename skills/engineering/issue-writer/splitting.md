# Specs and splitting

When work needs more than one ticket, write a **spec** first, then break it into **tracer-bullet** tickets that point back to it. The spec holds the shared intent and decisions; each ticket holds one slice of behavior.

Do not create a parent ticket with sub-issues. Linear has no epic concept, and fake parents become clutter. The spec is a Linear **document**; the tickets are standalone issues linked to it.

## 1. Write the spec

Synthesize what the conversation and recon already established. Interview the user only for gaps that block a decision. Create the document with `save_document`, linked to the project.

```markdown
# [Feature name]

## Problem
[The problem, from the user's view.]

## Solution
[The solution, from the user's view.]

## User stories
1. As a <actor>, I want <feature>, so that <benefit>
[A long, numbered list covering every part of the feature. Tickets trace back to these.]

## Decisions
- [Modules built or changed, and their interfaces]
- [Contracts, schema changes, architectural choices, specific interactions]

## Testing
- [The seams to test at — existing ones first, as high as possible, as few as possible]
- [Prior-art tests to model after]

## Out of scope
- [What this spec leaves alone, and why]

## Tickets
| Ticket | Delivers | Blocked by |
|--------|----------|------------|
[Filled in after the tickets exist.]

## Done when
- [ ] Every ticket above is Done
- [ ] [Feature-level acceptance, checkable on the default branch]
```

Name modules and interfaces, not file paths; paths go stale before the last ticket runs. A snippet that pins a decision (schema, type shape, state machine) may go under Decisions, trimmed to the decision.

## 2. Draft the tracer bullets

- Each ticket cuts a narrow but complete path through every layer it needs (schema, API, UI, tests). A finished ticket is demoable or checkable on its own.
- Each fits the [scoping rules](SKILL.md#scoping-rules): one PR, one fresh context window, green on its own.
- Prefactoring comes first. "Make the change easy, then make the easy change."
- Give each ticket its **blockers**: the tickets that must merge before it can start. Keep the graph shallow; most tickets should start right away.

A **wide refactor** (one mechanical change whose blast radius spans the codebase, like renaming a shared column) can't land as one green slice. Sequence it as **expand–contract**: expand (add the new form beside the old), then migrate callers in batches sized by blast radius (each blocked by the expand), then contract (delete the old form, blocked by every batch).

## 3. Quiz the user

Show the breakdown as a numbered list. For each ticket: title, what it delivers, and its blockers. Ask:

- Is the granularity right (too coarse / too fine)?
- Does each blocker gate the ticket for real?
- Do the test seams match their expectations?

Iterate until the user approves the breakdown.

## 4. Create the tickets

1. Create tickets in dependency order (blockers first), each a standalone issue using the [description template](SKILL.md#description-template), with the spec linked under Agent notes.
2. Set Linear's native `blockedBy` relations.
3. Fill the spec's Tickets table with the issue links.

[execute](../execute/SKILL.md) can run the whole spec: it works the **frontier** (every ticket whose blockers have merged) until the graph is done.
