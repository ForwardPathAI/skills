# Splitting large work

When a change is larger than ~4 focused hours, split it into multiple issues.

Honor the calling mode. In `draft`, produce the document and issue payloads below without calling any Linear write tool. In `create`, persist the approved or authorized payloads. In `update`, update only the named issue and return any additional issue/document drafts to the caller for a separate creation step. A caller that owns the grouping document, such as a delivery-plan workflow, supplies that document instead of creating a duplicate here.

**Do not** create a parent ticket with sub-issues. Linear has no epic concept, and fake parents become clutter.

**Do** create a Linear **document** that groups standalone issues:

1. Create or reuse the grouping document first. It describes the overall feature, lists tasks with dependencies, captures shared technical context, and defines feature-level acceptance criteria. Reuse the caller's document when supplied.
2. Create each task as a **standalone issue**, not a sub-issue.
3. Link the document URL in every issue's `Additional Context`.
4. Use Linear's `blocked by` / `blocks` issue relations for ordering.

On a partial rerun, reuse recorded document and issue IDs and create only missing items. Fill in the document's issue links after the issues exist. When replacing an oversized existing issue, preserve it and update its description with the agreed disposition and replacement links; do not close it or turn the new issues into children without a separate instruction.

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
