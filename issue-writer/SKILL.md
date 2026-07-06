---
name: issue-writer
description: Write Linear issues an AI coding agent can execute without follow-up questions. Use when the user wants to create a Linear issue/ticket/bug, or split a feature into multiple tickets.
---

# Linear Issue Writer

Every issue is a handoff to an **executor** with **zero context**: an AI coding agent (or unfamiliar developer) that has not seen this conversation, your repo survey, or any other issue. Assume it is competent at following explicit instructions and weak at filling gaps, recovering from ambiguity, or knowing when to stop. The issue is the product — its quality determines whether the executor succeeds. Output goes into Linear via the Linear MCP server, not a chat reply.

Three properties make an issue executable:

1. **Self-contained context** — everything needed is in the issue: paths, code excerpts, conventions, commands. If it references "the pattern we discussed," it is broken.
2. **Verification gates** — requirements and done criteria are commands with expected results, never judgments ("works correctly").
3. **Hard boundaries and escape hatches** — an explicit out-of-scope list, and STOP conditions so the executor reports back instead of improvising when reality doesn't match the issue.

## Hard rules

1. **Excerpts come from your own reads.** Open every file you cite before writing; paths and line numbers are facts you verified, not guesses.
2. **Never reproduce secret values.** Linear is an external system. If context includes credentials, tokens, or `.env` contents, reference the `file:line` and credential type only.
3. **Commands are verified, not guessed** — pulled from `package.json` / CI config / repo docs during recon.

## Workflow

1. **Recon** — read enough of the repo to write from evidence:
   - What changes, which repo/codebase, what the user is trying to accomplish.
   - Exact build / test / lint / typecheck commands — these become the issue's verification gates.
   - The conventions that apply (error handling, naming, folder layout) and one exemplar file the executor must match.
   - Intent docs where present (`CLAUDE.md`/`AGENTS.md`, ADRs, `CONTEXT.md`, `DESIGN.md`) — quote the specific lines that constrain this work; the executor has not read those docs.
   - Record `git rev-parse --short HEAD` — the issue stamps the commit it was written against, so the executor can detect drift.
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
| **Title** | Imperative mood, stating what will be true after the issue lands. "Add email validation to signup form", not "Signup issue". |
| **Description** | Required. Use the template below. |

## Description template

Fill every section. Use "None" for sections that don't apply — never omit.

```markdown
## Why this matters
[2–4 sentences: the problem, its concrete cost, what improves when this lands.
Intent is what lets the executor make a correct judgment call when a detail is off.]

## Current state

**Relevant files** (each with its role):
- `src/orders/api.ts` — order-list endpoint; contains the N+1 (lines 130–160)

**Excerpts** — the code as it exists today, short, with `file:line` markers,
enough that the executor can confirm it's looking at the right thing.

**Conventions to match** (with one exemplar):
- Error handling follows the Result pattern — see `src/lib/result.ts` and its
  use in `src/users/api.ts:40-60`. Match it.

## Commands

| Purpose   | Command                 | Expected on success |
|-----------|-------------------------|---------------------|
| Tests     | `pnpm test -- <filter>` | all pass            |
| Typecheck | `pnpm typecheck`        | exit 0, no errors   |

(Exact commands from this repo — verified during recon, not guessed.)

## Scope

**In scope** (the only files to modify):
- `src/orders/api.ts`
- `src/orders/api.test.ts` (create)

**Out of scope** (do NOT touch, even though they look related):
- [File or change, with one line on why it's excluded]

## Requirements
- [ ] [Specific, testable thing the executor must do — exact files and symbols]

## Test plan
- New tests to write: which file, covering which cases (happy path, the
  specific bug/regression, named edge cases).
- Which existing test to use as the structural pattern: "model after
  `src/users/api.test.ts`".

## Done criteria
Machine-checkable. ALL must hold:
- [ ] `<test command>` exits 0, including N new tests
- [ ] `<typecheck/lint command>` exits 0, no new errors
- [ ] No files outside the in-scope list are modified (`git status`)

## STOP conditions
Stop and comment on this issue instead of improvising if:
- The code at the "Current state" locations doesn't match the excerpts
  (the repo has drifted since this issue was written).
- A verification command fails twice after a reasonable fix attempt.
- The fix appears to require touching an out-of-scope file.
- [Any assumption specific to this issue that, if false, invalidates the approach]

## Dependencies
- **Blocked by:** [Issue refs, or None]
- **Blocks:** [Issue refs, or None]

## Additional context
Written against commit `<short SHA>`, <YYYY-MM-DD>.
[Error messages, screenshots, design links, doc URLs. Or None.]
```

## Scoping rules

Each issue must be:

- **Small** — completable in 1–4 hours of focused work.
- **Shippable** — produces a deployable, working change on its own.
- **Testable** — pass/fail criteria are objective.
- **Atomic** — one concern, one feature slice.

If you can't satisfy all four in one issue, split (see [Splitting large work](splitting.md)).

## Quality bar — check before creating each issue

- Could an executor that has never seen this repo start with only the issue and the repo? Any knowledge from this session must be inlined.
- Is every acceptance check a command with an expected result, not a judgment ("make sure it works")?
- Does every requirement name exact files and symbols, not "the relevant module"?
- Are the STOP conditions specific to this issue's actual risks, not boilerplate?
- **Bugs** include reproduction — error, steps, expected vs actual.
- Project, priority, and labels are set in Linear; dependencies stated or "None".
- No secret values anywhere in the issue — locations and credential types only.
- The commit SHA is filled in and the excerpts match what's live at that SHA.
