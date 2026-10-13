---
name: duplication
description: "Benedict review skill: duplicated logic (DRY) a change introduces, such as reimplementing a helper the codebase already has, copy-pasted blocks, and rules or constants defined in two places that must stay in sync."
metadata:
  benedict/review: "true"
---

# Duplication

Find knowledge the change duplicates, where the copies will drift apart and one of them will end up wrong.

## Look for

- **Reimplemented helpers**: new code that does what an existing function, hook, component, utility or installed dependency already does. Search the repository for similar names, key calls and string literals before deciding.
- **Copy-paste in the change**: blocks repeated with small edits, where fixing one would mean fixing the others.
- **Duplicated rules**: the same constant, validation, schema, mapping, permission check, path or URL defined in more than one place; a type written by hand to mirror one that exists or can be derived.
- **Parallel lists**: a new kind added to one switch, map or list while other places that enumerate the same kinds are not updated.

## How to confirm

Quote the new code and name the existing file and symbol it duplicates. Say what would drift if one copy changed, and what to reuse instead.

## Do not report

- Code that looks alike but encodes different rules that will change for different reasons.
- Two or three trivial lines, or test setup that reads better inline.
- Duplication that already existed, unless the change adds another copy.
- Extractions that would need flags or modes to cover the differences; that is worse than the duplication.
