---
name: auto-pilot-pr
description: Drive an open PR to merge. Runs maintain-pr until the latest head is ready, then arms GitHub auto-merge on that head so the PR merges itself once approval and required checks clear.
disable-model-invocation: true
---

# Auto-pilot PR

[maintain-pr](../maintain-pr/SKILL.md) gets a PR ready and stops short of merging. This skill adds the last step: once the latest head is ready, **arm** GitHub auto-merge, so the PR merges itself when what's left (often a human approval) clears.

The rule that keeps this safe: auto-merge stays armed only on a head you have verified as ready.

## Authorization

Invoking this skill authorizes everything maintain-pr does on this PR, plus arming auto-merge, or merging at once when GitHub has nothing left to wait for. For this PR only, it overrides maintain-pr's limits on merging and enabling auto-merge. If the repo requires no approval, the PR merges as soon as required checks pass, with no human review; say so when you arm it.

It does not authorize `--admin` merges or any other branch-protection bypass, approving the PR, dismissing reviews, changing repo settings, or merging other PRs.

## Preflight

Read [maintain-pr](../maintain-pr/SKILL.md) now; this skill runs its loop. If it isn't installed, stop and say so.

Then check that auto-merge can be armed. If any check fails, run maintain-pr alone and report why auto-merge stayed off.

- **Repo allows it**: `gh api graphql -f query='{repository(owner:"<owner>",name:"<repo>"){autoMergeAllowed}}'` returns `true`. Don't change the setting.
- **Not a draft.** Marking it ready is the user's call.
- **Base is the default branch** (or a release base the user named). In a stack, arm only the bottom PR; an upper layer would merge into its parent's branch. Report the others as waiting on their parent.

Merge method: the one the user named, else `gh repo view --json viewerDefaultMergeMethod` (`SQUASH` → `--squash`, `MERGE` → `--merge`, `REBASE` → `--rebase`).

## The loop

1. **Disarm before every push.** If auto-merge is armed (`gh pr view <pr> --json autoMergeRequest`), run `gh pr merge <pr> --disable-auto` before you push anything. A new commit is a head you haven't verified, and required checks alone could merge it before Greptile or you see it.
2. **Maintain.** Run maintain-pr's loop until it reports the latest head ready, or ready except for human approval. Don't count a head as ready while any human's latest review on the PR is "changes requested". Record the head SHA.
3. **Arm.**

   ```bash
   gh pr merge <pr> --auto --<method> --match-head-commit <ready-sha>
   ```

   `--match-head-commit` refuses to arm if the head moved after you verified it. GitHub does not re-check it later: a push by someone with write access while armed can still merge on required checks alone. Confirm with `gh pr view <pr> --json state,autoMergeRequest,headRefOid`. If GitHub refuses because the PR is already mergeable, run the same command without `--auto`.
4. **Watch or report.** If the PR merged, go to Finish. If it's armed and the host can wake you on PR activity (T3 Code: `watch_pull_request`), keep a watch, report the armed state, and end the turn. On wake, start again at step 1. If the host can't wake you, go to Finish. Don't poll for a human.

Anything that changes the PR while armed (new feedback, a failed check, auto-merge disarmed by GitHub, a base change) means a new pass from step 1.

## Finish

Finish when the PR has merged, is blocked, or is armed with no way to watch it. Remove any watch you registered, then report one state:

- **Merged**: merge commit SHA and method.
- **Armed**: head SHA, method, what GitHub is waiting on (whose approval, which checks), and, with no watch, that nothing will answer new feedback and a push by anyone with write access can merge without a new pass. Tell the user `gh pr merge <pr> --disable-auto` turns it off.
- **Blocked**: maintain-pr's blocker, or why auto-merge couldn't be armed.

Include maintain-pr's report: feedback dispositions, validation, and Greptile status. "Armed" is not "ready to merge"; say which one you mean.
