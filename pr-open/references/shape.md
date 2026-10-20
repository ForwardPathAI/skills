# PR shape

Pick one shape before filing issues or changing branches. Explicit user words win ("stack this" → stack; "one PR" → one PR). A prepared branch or a caller's fixed batch boundary is always one PR.

| Shape | Use when | Base |
|-------|----------|------|
| **One PR** | One concern, a reviewer can read it in one sitting, or the parts only make sense together | Default branch (or user-named base) |
| **Split** (independent PRs) | Two or more concerns with no dependency between them (a feature plus an unrelated fix or drive-by refactor) | Each PR on the default branch |
| **Stack** (dependent PRs) | Parts must land in order, and the whole is too big for one review | Each PR on the PR below it |

## Keep it as one PR when

- It is under ~400 changed lines of hand-written code (ignore lockfiles, generated code, snapshots, fixtures).
- The parts would break `main` if merged alone (a rename and all its callers; a migration and the code that requires it in the same deploy).
- Splitting would add more review overhead than it saves (tiny prep commits, one-line fixes).

## Split into independent PRs when

- The diff mixes unrelated concerns. Each concern gets its own PR, issue, and branch off the default branch.
- Pieces can merge in any order. If one piece needs another, that is a stack, not a split.

## Stack when all of these hold

- The work is over ~400 lines or spans several layers, and one reviewer pass would be hard.
- The pieces depend on each other in a clear order. Common layers, bottom to top:
  1. Prep refactor or mechanical change (rename, move, format) — no behavior change
  2. Schema, migration, or shared types
  3. Backend / API
  4. UI / client
- Each layer builds, passes tests, and is safe to merge alone. The bottom layer must be shippable to `main` without the layers above it.
- The user wants review to start before the whole feature is done, or is adding new work on top of a branch whose PR is still open.

## Don't stack when

- A layer can't build or pass tests without the one above it — merge those layers or reorder.
- The stack would go deeper than ~3–4 PRs. Rebases get painful; split by vertical slice instead (see issue-writer [splitting](../../issue-writer/splitting.md)).
- The parent PR is likely to churn a lot in review. Wait for it to settle, or keep the work in one PR.

## Base rules for a stack

- On a feature branch and stacking new work on top → base = current branch.
- On the default branch and the user asks to stack → ask which branch to stack on, or offer one PR on the default branch. Do not proceed until they answer.
- User names a base → use it.
- The base must exist on the remote. Push it first if it has no remote branch.

## Confirm before splitting

For one PR, proceed. For a split or stack, show the user the plan — each PR's title, files, rough size, and base — and wait for approval before filing issues.
