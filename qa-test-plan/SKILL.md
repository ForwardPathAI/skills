---
name: qa-test-plan
description: Add QA test cases to the Notion QA Test Plan database — generate candidates from a feature change or the whole app, get QA approval, then persist. Use when a feature ships or a PR opens and test coverage should be added, or when populating the plan for a new app.
---

# QA Test Plan

Maintain the **Notion QA Test Plan database** — the canonical store QA works through during full regression runs. Each row is one test case. This skill generates candidate cases, gets QA approval, and appends them.

**Each project has its own database**, created once by `qa-test-plan-setup` and titled `<Project> — QA Test Plan`. The live schema (properties, select options) is the source of truth — read it from Notion, never assume.

## Workflow

```
- [ ] Step 1: Locate the database
- [ ] Step 2: Gather context (feature or whole-app)
- [ ] Step 3: Generate candidates
- [ ] Step 4: QA review gate
- [ ] Step 5: Persist approved cases
```

### Step 1: Locate this project's database

Resolve the database in this order:

1. **Repo config** — read `qa/qa-config.yml` in the app repo; use its `notion_database:` URL.
2. **Search by project** — `notion-search` for `<Project> — QA Test Plan`, where `<Project>` is the app repo / project name. A title match on the wrong project is worse than no match — confirm the hit with the user if more than one is plausible.
3. **Ask** — request the database URL from the user. After they provide it, offer to save it to `qa/qa-config.yml` (`notion_database: <url>`) so future runs skip this step.

Then read the database schema (properties and select options).

If no database exists for this project, stop and tell the user to run `/qa-test-plan-setup` — do not create a database from this skill.

Done when: the right project's database is confirmed and its schema loaded.

### Step 2: Gather context

Two branches — pick from how you were invoked:

- **Feature-scoped** (the common case — a PR opened, a feature shipped): extract the feature name and what changed from the PR description, diff, and changed files.
- **Whole-app** (initial population): enumerate what a tester can exercise — routes, backend endpoint groups, feature flags — from the app repo. Run from the app repo root, not the skills repo.

Either way, query the database for existing rows touching this feature so candidates don't duplicate coverage.

Done when: you can list the feature scope and the existing coverage for it.

### Step 3: Generate candidates

For each behavior in scope, draft cases covering:

- Happy path — the feature works as intended
- Edge cases — boundaries, empty inputs, unusual states
- Error handling — invalid input, permission failures
- Integration — where this feature touches others
- Regression risk — existing behavior the change could break

Present the candidates as a table: **Test Case | Feature | Steps | Expected Result | Category | Priority**. Use only Feature, Category, and Priority options that exist in the live schema. Mark any candidate that overlaps an existing row as `possible duplicate of <row>` instead of silently including or dropping it.

Done when: every candidate is shown to the user with steps and expected result — no stubs.

### Step 4: QA review gate

This is a hard stop. Ask QA to approve, edit, drop, or add cases. Do not write anything to Notion until they confirm the final set.

Done when: the user has explicitly confirmed the final set.

### Step 5: Persist approved cases

`notion-create-pages` — one row per approved case, with `Feature` set and `Status: Not Started`. Append only: never edit or delete rows QA already owns (existing statuses are regression history).

Done when: rows written equals cases approved, verified by re-querying the database. Report the count and the database link.

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Writing to Notion before QA confirms | The review gate is the point — wait |
| Inventing routes/endpoints/behavior not in the app | Only cover what exists in code |
| Editing or deleting existing rows | Append only; statuses are regression history |
| Silently skipping duplicates | Flag them for QA to decide |
| Hardcoding Feature/Category/Priority options | Read the live schema |

## Related

- `qa-test-plan-setup` — creates the database and defines the schema.
- When a generated case reveals a product gap, file it with the `issue-writer` skill.
