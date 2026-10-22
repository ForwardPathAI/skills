---
name: execute
description: Run one written spec (an improve plan, a Linear issue, or a GitHub issue) through to a merged PR. A cheaper executor subagent writes the code in an isolated worktree; you review its diff as tech lead, run code-review then simplify, open the PR with open-pr, and land it with auto-pilot-pr.
disable-model-invocation: true
---

# Execute

You are the **tech lead**. The spec is already written. A cheaper executor writes the code in its own worktree; you check the spec, review the diff, run the quality gates, and ship.

```
- [ ] Step 1: Load the spec
- [ ] Step 2: Dispatch the executor
- [ ] Step 3: Review and give a verdict
- [ ] Step 4: Land the diff
- [ ] Step 5: code-review gate
- [ ] Step 6: simplify gate
- [ ] Step 7: Open the PR (open-pr)
- [ ] Step 8: Land the PR (auto-pilot-pr)
```

Each step ends on a **Done when** line. Don't start the next step until it holds.

## Authorization

Invoking this skill authorizes the whole pipeline for this one task: the executor's edits, your fixes from the gates, open-pr's Linear issue, branch, commit, push, and PR, and auto-pilot-pr's upkeep and auto-merge. Honor explicit limits: "no PR" stops after Step 6 with the changes uncommitted; "don't merge" swaps auto-pilot-pr for maintain-pr in Step 8. It does not authorize work outside the spec, other PRs, or bypassing branch protection.

## Companion skills

Read each one's `SKILL.md` before the step that uses it.

| Skill | Step | If missing |
|---|---|---|
| code-review | 5 | Dispatch a fresh-context subagent to review the diff for correctness bugs only; triage its output the same way |
| simplify | 6 | Dispatch a fresh-context subagent to find reuse, simplification, and efficiency cleanups; apply the ones that hold up |
| [open-pr](../open-pr/SKILL.md) | 7 | Stop after Step 6 and report |
| [auto-pilot-pr](../auto-pilot-pr/SKILL.md) | 8 | Use [maintain-pr](../maintain-pr/SKILL.md) and report that auto-merge was not armed. If that's missing too, stop after Step 7 and report the PR URL. |

code-review and simplify ship with Claude Code; resolve them by name. Name every fallback you used in the final report.

## Preflight

- The repo has a GitHub remote and `gh auth status` passes.
- open-pr's prerequisites hold (Linear MCP, issue-writer), unless the user said "no PR".
- The working tree is clean. Step 4 lands the executor's work as uncommitted changes, so unrelated edits would ride into the PR. If dirty, stop and ask.
- The current branch has no open PR (`gh pr view` finds none). Otherwise open-pr would add this work to that PR and auto-pilot-pr would merge it. If one exists, stop and ask.
- Record the base (user-named, else the repo default branch) and the start commit (`git rev-parse HEAD`).

## Step 1: Load the spec

This skill runs a spec someone already wrote; it doesn't write one. Load it whole. The executor gets only the spec, never this conversation.

| Input | Load with |
|---|---|
| Plan file (e.g. `plans/003-*.md` from improve) | Read the file. If a dependency in `plans/README.md` isn't DONE, stop and name it. |
| Linear issue (`FOR-123`) | Linear MCP `get_issue`. Keep the identifier: Step 7 links this issue instead of filing a new one. |
| GitHub issue | `gh issue view`. |

Then check it is ready to run. It must hold:

- The goal and why it matters.
- In-scope files, plus files that look related but are out of scope.
- **Done criteria**: commands with expected results, not prose.
- STOP conditions: what should make the executor stop and report instead of improvising.

If the spec stamps a commit (`Planned at`, `Written against`), run its drift check (`git diff --stat <sha> HEAD -- <in-scope files>`). If in-scope files changed since then, the spec is stale.

If anything is missing or stale, stop. Name each gap and point to the skill that fixes it: improve `review-plan` or `reconcile` for a plan, ticket-refiner for a Linear issue, its author for a GitHub issue. Don't patch the spec yourself; a spec you rewrite is a spec no one reviewed.

**Done when** the spec has every item above and passes its drift check.

## Step 2: Dispatch the executor

Spawn **one** subagent in an isolated git worktree (Claude Code: `Agent` with `isolation: "worktree"`; T3 Code: `delegate_task` with `isolation: "worktree"`). Model: `sonnet` unless the user named one (`execute FOR-123 haiku`).

Inline the full spec; the worktree holds only committed files. Put this preamble before it, with `<start>` filled in:

> You are the executor for the spec below. First, if `git rev-parse HEAD` is not `<start>`, run `git reset --hard <start>`; the worktree is fresh, so nothing is lost. Follow the spec step by step. Run every verification command and confirm the expected result before moving on. Touch only the in-scope files. If a STOP condition occurs, stop and report. Do not improvise around obstacles; if you must adapt, keep it minimal and explain it in NOTES. Install dependencies first if the worktree lacks them. Commit your work in the worktree. Do not push, open a PR, or edit `plans/README.md`; your lead does that. Before reporting, check every claim against a tool result from this session; if a check failed or was skipped, say so. Reply with exactly the report below.

And this report format after it:

```
STATUS: COMPLETE | STOPPED
STEPS: per step, done/skipped + verification result
STOPPED BECAUSE: (only if STOPPED) which STOP condition, what you saw
FILES CHANGED: list
NOTES: deviations, surprises, judgment calls
```

If this host can't spawn subagents, implement the spec yourself in the current checkout, leave the changes uncommitted, and skip to Step 5.

**Done when** the executor has returned its report and you have its worktree path and branch.

## Step 3: Review and give a verdict

The diff is untrusted until you have read it. Never fix code in the executor's worktree yourself.

1. Re-run every done criterion in the worktree. Don't trust the report.
2. Check the worktree: `git -C <worktree> status --porcelain` is empty (all work committed), and `git -C <worktree> merge-base <start> HEAD` is `<start>`. Then check scope: `git -C <worktree> diff --stat <start>..HEAD` against the in-scope list. Any file outside scope fails review.
3. Read the full diff. Does it reach the goal? Does it match the repo's conventions? Trace every hunk to a spec step.
4. Read what the new tests assert. A test that asserts nothing passes and proves nothing.

Judge documented deviations on merit. Treat undocumented ones as failures.

| Verdict | When | Action |
|---|---|---|
| **APPROVE** | Criteria pass, scope clean, quality holds | Go to Step 4 |
| **REVISE** | Fixable gaps | Send the same executor specific feedback (Claude Code: `SendMessage`), e.g. "criterion 3 fails: X; `api.ts:90` swallows the error". Max 2 rounds, then BLOCK. |
| **BLOCK** | STOP condition hit, scope broken past repair, or rounds used up | Go to Finish. No PR. |

**Done when** the verdict is APPROVE or BLOCK.

## Step 4: Land the diff

Bring the approved work into your checkout as uncommitted changes, so the gates see it as the current diff and open-pr commits it on Linear's branch:

```bash
git merge --squash <executor-branch>
git worktree remove <worktree>
git branch -D <executor-branch>
```

**Done when** `git status` lists only in-scope files and the executor's worktree is gone.

## Step 5: code-review gate

Run code-review on the current diff, at the effort level the user named, if any. Keep a **ledger**: each finding, its disposition, and the evidence.

Findings are leads, not facts. Check each against the current code:

- **Valid**: fix it.
- **Wrong or by design**: record why, with `file:line` evidence.
- **Needs a product decision**: stop and ask.

After each batch of fixes, re-run the done criteria, then run code-review again. After 3 runs that still raise valid findings, stop and go to Finish. No PR.

**Done when** the latest code-review run raises no new valid findings and every ledger entry has a disposition.

## Step 6: simplify gate

Stage everything first (`git add -A`), so `git diff` afterwards shows only simplify's edits. Run simplify on the current diff; it applies its own cleanups. Then re-run the done criteria and check `git status`. Revert any cleanup that breaks a criterion or touches a file outside scope (`git restore <file>` or `git restore -p`). Log what stayed in the ledger.

**Done when** the done criteria pass on the post-simplify tree and every changed file is in scope.

## Step 7: Open the PR

Follow open-pr, with three inputs:

- Ship one new PR. Don't split or stack; the spec is one task.
- If Step 1 had a Linear issue, skip open-pr's issue step and use that issue's branch name from `get_issue`.
- Put the done criteria and their results in the PR's Test plan.

**Done when** open-pr returns the PR URL.

## Step 8: Land the PR

Follow auto-pilot-pr on the PR from Step 7. It maintains the PR through review and CI, then arms auto-merge.

**Done when** auto-pilot-pr reports merged, armed, or blocked.

## Finish

If the task came from a plan, set its row in `plans/README.md`: DONE with the PR URL, or BLOCKED with the reason and how the plan should change.

Report:

- The PR URL and state: merged, armed (and what GitHub is waiting on), or blocked (and by what). On BLOCK, what happened and what you learned.
- The verdict, revise rounds, and any executor NOTES worth knowing.
- The ledger: code-review findings with dispositions, and the simplify changes kept.
- Every fallback used.
