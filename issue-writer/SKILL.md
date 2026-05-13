---
name: issue-writer
description: Write Linear issues that an AI coding agent can execute without follow-up questions. Use whenever the user asks to create, draft, file, or break down a Linear issue, ticket, task, story, bug, or epic — including breaking a feature into multiple tickets. Triggers on phrases like "create a Linear issue", "file a ticket", "make a Linear task", "write up a bug", or "split this into tickets".
---

# Linear Issue Writer

Produce Linear issues that are small, shippable, and unambiguous to an AI coding agent. The output goes into Linear via the Linear MCP server — not into a chat reply.

## Workflow

1. **Gather context** — what is the change, which repo/codebase, what's the user trying to accomplish.
2. **Resolve the project** — required field. If the user didn't name one, infer from the repo (folder name or `.git/config` remote) and confirm before writing.
3. **Fetch labels and projects from Linear via MCP** — never invent label names; only apply labels that exist in the workspace.
4. **Scope** — if the change is larger than ~4 focused hours, split into multiple issues backed by a Linear document (see [Splitting large work](#splitting-large-work)).
5. **Write** — follow the [Description template](#description-template). Fill every section or write "None" — do not delete sections.
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

If you can't satisfy all four in one issue, split.

## Splitting large work

**Do not** create a parent ticket with sub-issues. Linear has no epic concept, and fake parents become clutter.

**Do** create a Linear **document** that groups standalone issues:

1. Create the document first — describes the overall feature, lists tasks with dependencies, captures shared technical context, defines feature-level acceptance criteria.
2. Create each task as a **standalone issue**, not a sub-issue.
3. Link the document URL in every issue's `Additional Context`.
4. Use Linear's `blocked by` / `blocks` issue relations for ordering.

Prefer splitting by **vertical slice** (end-to-end for a small piece) over horizontal layers.

### Document template

```markdown
# [Feature name]

## Overview
[What this feature does and why.]

## Tasks
| Issue | Description | Blocked by |
|-------|-------------|------------|
| [link] | API endpoint | None |
| [link] | UI component | None |
| [link] | Wire UI to API | Issues above |

## Technical Context
[Shared decisions, patterns, conventions that apply across all tasks.]

## Done When
- [ ] All linked issues completed
- [ ] [Feature-level acceptance criteria]
```

## Before submitting

Verify the issue:

- [ ] **Project, priority, labels** are set in Linear.
- [ ] **File paths** are specific (real paths from the repo).
- [ ] **Patterns/libraries** are named (no "use best practices").
- [ ] **Acceptance criteria** are objectively verifiable.
- [ ] **Out of scope** is explicit.
- [ ] **Dependencies** are stated, or "None".
- [ ] A developer unfamiliar with the project could start work without asking a question.

## Anti-patterns

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| "Improve performance" | No target | "Reduce `/users` p95 from 2s to <200ms" |
| "Fix the bug" | No reproduction | Include error, steps, expected vs actual |
| "Refactor auth" | Too broad | Split into specific refactors with bounded scope |
| Missing file paths | Forces agent to guess | Always include real paths |
| "Use best practices" | Subjective | Name the pattern or example file |
| Parent ticket with sub-issues | Linear has no epics | Use a Linear document instead |
| Inventing labels | Won't apply | Only use labels that exist in the workspace |
