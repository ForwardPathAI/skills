---
name: issue-writer
description: Write Linear issues an AI coding agent can execute without follow-up questions. Use when the user wants to create a Linear issue/ticket/bug, or split a feature into multiple tickets.
---

# Linear Issue Writer

Produce Linear issues an AI coding agent can execute without follow-up questions: small, shippable, unambiguous. The output goes into Linear via the Linear MCP server — not into a chat reply.

## Workflow

1. **Gather context** — what is the change, which repo/codebase, what's the user trying to accomplish.
2. **Resolve the project** — required field. If the user didn't name one, infer from the repo (folder name or `.git/config` remote) and confirm before writing.
3. **Fetch labels and projects from Linear via MCP** — never invent label names; only apply labels that exist in the workspace.
4. **Scope** — if the change is larger than ~4 focused hours, split into multiple issues (see [Splitting large work](splitting.md)).
5. **Write** — follow the [Description template](#description-template).
6. **Create via Linear MCP** with all required fields set.

## Required fields (every issue)

| Field | Rule |
|-------|------|
| **Project** | Required. Infer from repo name if absent; confirm with user before creating. |
| **Priority** | Required. Urgent / High / Medium / Low. Default Medium if unspecified. |
| **Labels** | Required. Pull from Linear; apply only existing labels. |
| **Title** | Imperative mood, specific. "Add email validation to signup form", not "Signup issue". |
| **Description** | Required. Use the template below. |

## Description template

Fill every section. Use "None" for sections that don't apply — never omit.

```markdown
## Summary
[1–2 sentences: what changes and why.]

## Technical Context

**Relevant files:**
- `path/to/file.ts` — [why it's relevant]

**Patterns / libraries to use:**
- [Existing utility, component, or pattern to follow with file path]

**Similar existing code:**
- `path/to/example.ts:45-67` — [what it does that's analogous]

## Requirements
- [ ] [Specific, testable thing the agent must do]

## Acceptance Criteria
- [ ] [How to verify the requirement is met]
- [ ] Tests pass
- [ ] No new type or lint errors

## Out of Scope
- [Explicitly excluded — prevents scope creep]

## Dependencies
- **Blocked by:** [Issue refs, or None]
- **Blocks:** [Issue refs, or None]

## Additional Context
[Error messages, screenshots, design links, doc URLs. Or None.]
```

## Scoping rules

Each issue must be:

- **Small** — completable in 1–4 hours of focused work.
- **Shippable** — produces a deployable, working change on its own.
- **Testable** — pass/fail criteria are objective.
- **Atomic** — one concern, one feature slice.

If you can't satisfy all four in one issue, split (see [Splitting large work](splitting.md)).

## Before submitting

Verify the issue — the bar is that a developer unfamiliar with the project could start without follow-up questions:

- [ ] **Project, priority, labels** are set in Linear.
- [ ] **File paths** are specific — real paths from the repo, not guesses.
- [ ] **Patterns/libraries** are named — not "use best practices" but "follow the retry helper in `lib/http.ts`".
- [ ] **Requirements** are measurable — not "improve performance" but "reduce `/users` p95 from 2s to <200ms".
- [ ] **Bugs** include reproduction — error, steps, expected vs actual.
- [ ] **Acceptance criteria** are objectively verifiable.
- [ ] **Out of scope** is explicit.
- [ ] **Dependencies** are stated, or "None".
