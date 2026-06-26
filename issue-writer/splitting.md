# Splitting large work

When a change is larger than ~4 focused hours, split it into multiple issues.

**Do not** create a parent ticket with sub-issues. Linear has no epic concept, and fake parents become clutter.

**Do** create a Linear **document** that groups standalone issues:

1. Create the document first — describes the overall feature, lists tasks with dependencies, captures shared technical context, defines feature-level acceptance criteria.
2. Create each task as a **standalone issue**, not a sub-issue.
3. Link the document URL in every issue's `Additional Context`.
4. Use Linear's `blocked by` / `blocks` issue relations for ordering.

Prefer splitting by **vertical slice** (end-to-end for a small piece) over horizontal layers.

## Document template

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
