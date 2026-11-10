---
name: execute
description: Run a written ticket (Linear issue, GitHub issue, or improve plan) or a whole spec of tickets through to PRs that have merged or are armed to merge. A cheaper executor subagent writes each ticket's code in an isolated worktree; you review its diff as tech lead, run code-review then simplify, open the PR with open-pr, and land it with auto-pilot-pr. A spec runs its ticket graph frontier by frontier.
disable-model-invocation: true
---

# Execute

You are the **tech lead**. The work is already written. A cheaper executor writes the code in its own worktree; you orient it, review the diff, run the quality gates, and ship.

| Input | Mode |
|---|---|
| One ticket: Linear issue (`FOR-123`), GitHub issue, or plan file (`plans/003-*.md` from improve) | **Ticket**: run Steps 1–8 once. |
| A spec: Linear document, Linear project, or several tickets | **Spec**: read [Spec mode](references/spec.md) now; it runs Steps 1–8 for each ticket in the graph. |

```
- [ ] Step 1: Load and orient
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

Invoking this skill authorizes the whole pipeline for each ticket it runs: the executor's edits, your fixes from the gates, open-pr's branch, commit, push, and PR, and auto-pilot-pr's upkeep and auto-merge. Honor explicit limits: "no PR" stops after Step 6 with the changes uncommitted; "don't merge" swaps auto-pilot-pr for maintain-pr in Step 8; a named round or run limit caps Steps 3 and 5. It does not authorize work outside the ticket, other PRs, or bypassing branch protection. Only a user-approved decision changes a ticket's requirements.

## Read the ticket for intent

A ticket binds on four things: its **goal**, its **acceptance criteria** (done criteria, requirements), its **out-of-scope** list, and its **decisions**. Everything in it that points at code — file paths, line numbers, excerpts, a list of in-scope files, a commit stamp — is a **lead** from the day it was written. Code moves. Follow the behavior to where it lives now and change what the outcome needs. Touching a file the ticket never named is normal; touching something its out-of-scope list names is not. Stop rules and done criteria about files (a path moved, a file outside a listed set, an excerpt that no longer matches, "all changed files are in the in-scope list") are leads too; Step 3's hunk-by-hunk check replaces them.

Resolve on your own, and note in the PR: renamed or moved code, a changed command that tests the same behavior, criteria the code already meets, and any fix inside the ticket's outcome.

**Ask for a decision** only when:

- the outcome needs a behavior, contract, or schema change the ticket doesn't cover or rules out;
- acceptance criteria conflict with the code or with each other, or could pass only by weakening them;
- the work would cross an out-of-scope item;
- a ticket-specific "Ask first" or STOP condition about behavior holds; or
- a blocker hasn't merged.

To ask, preserve completed work, then present (with the host's question tool, or in chat):

- What you found, with code, history, or command evidence.
- The ticket item that blocks you.
- The exact ticket edit you propose, before and after, and what it adds, drops, or weakens. If no edit would help, name the outside action or decision needed.

Offer: approve and continue, approve with edits, or stop. On approval, re-read the ticket, apply only the approved edit (Linear `save_issue` with `patch`; `gh issue edit`; or the plan file), add a comment recording the change and the user's answer, read it back, and resume at the blocked step with the refreshed brief. If the source can't be edited, carry the approved change in the brief and report the edit as pending. Silence is not approval: if the user can't be reached, return the proposal to the parent when delegated, or finish with BLOCK and the resume point.

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

- `git remote get-url origin` points at GitHub (open-pr pushes to `origin`) and `gh auth status` passes.
- open-pr's prerequisites hold (Linear MCP, issue-writer), unless the user said "no PR".
- The working tree is clean. Step 4 lands the executor's work as uncommitted changes, so unrelated edits would ride into the PR. If dirty, stop and ask.
- The current branch has no open PR (`gh pr view` finds none). Otherwise open-pr would add this work to that PR. If one exists, stop and ask.
- Record the base (user-named, else the repo default branch) and the start commit (`git rev-parse HEAD`).

## Step 1: Load and orient

| Input | Load with |
|---|---|
| Linear issue | `get_issue` with relations, plus `list_comments`. Keep the identifier: Step 7 links it instead of filing a new one. Load the spec document if Agent notes links one. |
| GitHub issue | `gh issue view --comments`. |
| Plan file | Read the file. Check its dependencies in `plans/README.md`. |

Check the ticket is ready: a goal, checkable acceptance criteria, and an out-of-scope list (or "None"). An unmerged blocker or a missing item is a decision: ask, proposing the smallest fill. If the user stops, point to ticket-refiner for a Linear issue, improve `review-plan` for a plan, or its author for a GitHub issue.

Then **orient**. Start from the ticket's leads, but find where each piece of behavior lives now: search for the symbols and behavior, read the current code and its tests, and pick the test seam. Confirm each verification command against `package.json` or CI; swap in the current command when it tests the same behavior with the same expected result. Run the acceptance criteria that can run today.

Write the **brief**: the ticket as written, plus your orientation notes — where the behavior lives now, the verified commands, the test seam, and any criteria already met.

**Done when** each acceptance criterion maps to the code that will change or to evidence it already holds, and every verification command runs. If every criterion already holds, go to Finish with **ALREADY SATISFIED** and the evidence; open no PR.

## Step 2: Dispatch the executor

Spawn **one** subagent in an isolated git worktree (Claude Code: `Agent` with `isolation: "worktree"`; T3 Code: `delegate_task` with `isolation: "worktree"`). Model: `sonnet` unless the user named one (`execute FOR-123 haiku`).

The worktree holds only committed files, so inline the brief. Name the ticket and spec so the executor can fetch more if it has Linear access. Put this preamble before the brief, with `<start>` filled in:

> You are the executor for the brief below. First, if `git rev-parse HEAD` is not `<start>`, run `git reset --hard <start>`; the worktree is fresh, so nothing is lost. The goal, acceptance criteria, out-of-scope list, and decisions bind. File paths, excerpts, and file lists are leads: if code has moved, follow the behavior and change what the outcome needs, and nothing it doesn't. Write the test at the brief's seam first and watch it fail, then make it pass. Typecheck and run single test files as you go; run the full suite once at the end. Return STOPPED only for a decision: a behavior, contract, or schema change the brief doesn't cover; crossing an out-of-scope item; criteria that can't pass without weakening them; a ticket "Ask first" condition; or a check that still fails after two real fix attempts. Install dependencies if the worktree lacks them. Commit your work in the worktree. Do not push, open a PR, write to Linear or GitHub, or edit `plans/README.md`; report to your lead instead. Before reporting, check every claim against a tool result from this session; if a check failed or was skipped, say so. Reply with exactly the report below.

And this report format after it:

```
STATUS: COMPLETE | STOPPED
CRITERIA: per acceptance criterion, pass/fail + the command or evidence
STOPPED BECAUSE: (only if STOPPED) the decision needed, with evidence and a proposed answer
FILES CHANGED: list, one line each on why
NOTES: where code had moved from the ticket's leads, deviations, judgment calls
```

If this host can't spawn subagents, implement the brief yourself in the current checkout, leave the changes uncommitted, and skip to Step 5.

**Done when** the executor has returned its report and you have its worktree path and branch.

## Step 3: Review and give a verdict

The diff is untrusted until you have read it. Never fix code in the executor's worktree yourself.

1. Re-run every acceptance criterion with the brief's commands. Don't trust the report.
2. Check the worktree: `git -C <worktree> status --porcelain` is empty (all work committed), and `git -C <worktree> merge-base <start> HEAD` is `<start>`.
3. Read the full diff (`git -C <worktree> diff <start>..HEAD`). Trace every hunk to an acceptance criterion or to what it needs (a caller, a moved type, a test). A hunk that serves neither, or that touches an out-of-scope item, fails review. Does the change match the repo's conventions?
4. Read what the new tests assert. A test that asserts nothing passes and proves nothing.

Judge documented deviations on merit. Treat undocumented ones as failures. If the executor stopped, check its evidence: answer it yourself when the ticket already settles it (REVISE), else ask for a decision.

| Verdict | When | Action |
|---|---|---|
| **APPROVE** | Criteria pass, every hunk traces to the outcome, quality holds | Go to Step 4 |
| **REVISE** | Fixable gaps | Send the same executor specific feedback (Claude Code: `SendMessage`), e.g. "criterion 3 fails: X; `api.ts:90` swallows the error". Repeat until no gaps remain. |
| **BLOCK** | A decision only the user can make, or the loop stalls: the same gap survives three rounds | Ask for a decision. On approval, REVISE with the refreshed brief. Otherwise preserve work and report BLOCK. No PR while blocked. |

**Done when** the verdict is APPROVE, or BLOCK has been asked about without authorization to resume.

## Step 4: Land the diff

Bring the approved work into your checkout as uncommitted changes, so the gates see it as the current diff and open-pr commits it on Linear's branch:

```bash
git merge --squash <executor-branch>
git worktree remove <worktree>
git branch -D <executor-branch>
```

**Done when** `git status` lists only the approved files and the executor's worktree is gone.

## Step 5: code-review gate

Run code-review on the current diff, at the effort level the user named, if any. Keep a **ledger**: each finding, its disposition, and the evidence.

Findings are leads, not facts. Check each against the current code:

- **Valid**: fix it.
- **Wrong or by design**: record why, with `file:line` evidence.
- **Needs a product decision**: ask for a decision.

After each batch of fixes, re-run the acceptance criteria, then run code-review again. Repeat while the latest run raises any valid finding, new or repeated. If the loop stalls (the same finding survives three fix attempts, or a fix brings back one already fixed), ask for a decision. No PR while blocked.

**Done when** the latest code-review run raises no valid findings and every ledger entry has a disposition.

## Step 6: simplify gate

Stage everything first (`git add -A`), so `git diff` then shows only simplify's edits. Run simplify on the current diff; it applies its own cleanups. Then re-run the acceptance criteria. Revert any cleanup that breaks a criterion or reaches past the ticket's outcome (`git restore <file>` or `git restore -p`). Log what stayed in the ledger.

A cleanup can change behavior. If any stayed, run code-review again and handle its findings as in Step 5. If a finding traces to a cleanup, revert that cleanup rather than fix around it.

**Done when** the acceptance criteria pass on the post-simplify tree and code-review raises no valid findings on it.

## Step 7: Open the PR

Follow open-pr, with these inputs:

- Ship one new PR for the ticket. Don't split or stack unless spec mode says to.
- If Step 1 had a Linear issue, skip open-pr's issue step and use that issue's branch name from `get_issue`.
- Put the acceptance criteria and their results in the PR's Test plan.
- In the description, note where the code had moved from the ticket's leads, criteria met before this work, and any approved ticket edit.

**Done when** open-pr returns the PR URL.

## Step 8: Land the PR

Follow auto-pilot-pr on the PR from Step 7. It maintains the PR through review and CI, then arms auto-merge.

**Done when** auto-pilot-pr reports merged, armed, or blocked.

## Finish

If the ticket came from a plan, set its row in `plans/README.md`: DONE with the PR URL once merged; IN PROGRESS with the PR URL while armed or open; BLOCKED with the reason. For ALREADY SATISFIED, record DONE with the evidence. Armed is not merged.

Report:

- The PR URL and state: merged, armed (and what GitHub is waiting on), or blocked (and by what). For ALREADY SATISFIED, the evidence instead of a PR.
- Where the code had moved from the ticket's leads.
- Every decision asked: the question, the user's answer or that it's pending, and whether the ticket edit was confirmed.
- The verdict, revise rounds, and executor NOTES worth knowing.
- The ledger: code-review findings with dispositions, and the simplify changes kept.
- Every fallback used.
