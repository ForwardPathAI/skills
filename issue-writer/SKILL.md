---
name: issue-writer
description: Draft, create, or update Linear issues an AI coding agent can execute without follow-up questions. Use for issue authoring, splitting work, or when another skill needs an executable issue draft.
---

# Linear Issue Writer

Every issue is a handoff to an **executor** with **zero context**: an AI coding agent or unfamiliar developer that has not seen this conversation, your repo survey, or any other issue. Include the evidence and boundaries needed to implement and verify the work. The selected mode determines whether the result is a draft or a Linear write.

Three properties make an issue executable:

1. **Self-contained context** — everything needed is in the issue: paths, code excerpts, conventions, commands. If it references "the pattern we discussed," it is broken.
2. **Verification gates** — requirements and done criteria are commands with expected results, never judgments ("works correctly").
3. **Hard boundaries and escape hatches** — an explicit out-of-scope list, and STOP conditions so the executor reports back instead of improvising when reality doesn't match the issue.

## Hard rules

1. **Excerpts come from your own reads.** Open every file you cite before writing; paths and line numbers are facts you verified, not guesses.
2. **Never reproduce secret values.** Linear is an external system. If context includes credentials, tokens, or `.env` contents, reference the `file:line` and credential type only.
3. **Commands are verified, not guessed** — pulled from `package.json` / CI config / repo docs during recon.

## Modes and handoff

Select the mode before starting. Honor the caller's explicit mode. Otherwise a request to draft or propose uses `draft`, a request to create/file uses `create`, and a request to edit an identified issue uses `update`. If writing intent is unclear, return a draft.

| Mode | Inputs | Result and write boundary |
|---|---|---|
| `draft` | Scope, repository evidence, known placement, optional existing issue | Return title, full description, proposed fields, dependencies, and unresolved questions. No Linear writes, including comments, documents, or split issues. |
| `create` | New issue scope or a complete draft, resolved required fields, authorization to create | Reuse an existing issue for this exact work or create once. Return ID, identifier, URL, and Linear branch name. |
| `update` | Existing issue ID, intended field changes or approved draft, authorization to update | Update that issue only. Preserve unrelated fields, discussion, and relations; never create a replacement issue. Return its ID/URL and changed fields. |

The caller passes any approval already obtained, repository commit, excerpts, verified commands, and known workspace IDs. Reuse evidence that still matches the repository instead of repeating recon or interviews. If a caller requires review before saving, remain in `draft` until that review is satisfied. Do not ask again for an unchanged draft the user already approved.

Linear MCP is required for `create` and `update`. In `draft`, use read tools when available; if unavailable, leave unknown workspace IDs/labels explicitly unresolved rather than inventing them. An unresolved draft can be returned for discussion but must not be described as execution-ready.

For an update limited to metadata, links, or relations, inspect the target and validate those changes without regenerating its description or rerunning unrelated repository recon. Defaults apply to new issues; do not reset an existing issue's team, project, priority, labels, or content to defaults. A description rewrite must pass the template and quality bar, or explicitly retain unresolved gaps for review.

## Workflow

1. **Recon** — read enough of the repo to write from evidence:
   - What changes, which repo/codebase, what the user is trying to accomplish.
   - Exact build / test / lint / typecheck commands — these become the issue's verification gates.
   - The conventions that apply (error handling, naming, folder layout) and one exemplar file the executor must match.
   - Intent docs where present (`CLAUDE.md`/`AGENTS.md`, ADRs, `CONTEXT.md`, `DESIGN.md`) — quote the specific lines that constrain this work; the executor has not read those docs.
   - Record `git rev-parse --short HEAD` — the issue stamps the commit it was written against, so the executor can detect drift.
2. **Resolve workspace values** — fetch teams, projects, and labels from Linear via MCP, or reuse verified values from the caller. Never invent names. Draft mode may leave unavailable values unresolved.
3. **Resolve placement without routine confirmation** — honor any team/project the user named. Otherwise infer from the repo name, git remote, existing issues, and session context. Use a clearly matching project when one exists. If no suitable project exists, select the known team without a project; do not create a project or attach unrelated work to one merely to fill the field. Ask only when the team is unknown or multiple plausible placements remain ambiguous. A clear inferred placement or the absence of a project does not require approval. Draft mode can return unresolved placement for later resolution.
4. **Scope** — if the change is larger than ~4 focused hours, split into multiple issues (see [Splitting large work](splitting.md)).
5. **Write** — follow the [Description template](#description-template).
6. **Return or save according to mode** after applying the quality bar below:
   - `draft`: return the complete proposed issue payload and any unresolved gaps. For a split, also return the grouping-document draft and standalone issue drafts per [splitting.md](splitting.md). Stop before any write.
   - `create`: check supplied issue links and matching work in the resolved team/project before creating. Reuse a verified match; a similar title alone is not proof. Create via Linear MCP only when no matching issue exists. Fetch the result for its ID, URL, and branch name. After an uncertain write result, check whether it succeeded before retrying.
   - `update`: fetch the target and compare it with the draft's source version. Preserve unrelated concurrent changes; resolve conflicting edits before saving. Send only intended fields using the existing issue ID. If splitting requires new issues, return those drafts for an explicit `create` handoff; update mode itself creates none.

Creating and updating preserve literal Markdown newlines. Callers that receive a saved result must not repeat its write. A split run records created IDs and resumes missing items after a partial failure rather than duplicating them.

## Required fields (every issue)

| Field | Rule |
|-------|------|
| **Team** | Required. Use the team named by the user or established by repo/workspace context. |
| **Project** | Optional. Follow the placement rules above; omit it or pass `null` for a team-only issue. |
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
- Team, priority, and labels are set in Linear; project follows the placement rules and may be absent; dependencies stated or "None".
- No secret values anywhere in the issue — locations and credential types only.
- The commit SHA is filled in and the excerpts match what's live at that SHA.
