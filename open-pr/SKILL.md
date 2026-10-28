---
name: open-pr
description: Open or update GitHub PRs from local changes, with screenshots for UI changes and support for independent or stacked PRs. Honors no-Linear workflows and existing issue links. Use when asked to open, split, stack, or submit a PR.
---

# Open pull request

Publish the requested work as reviewable PRs. Honor explicit limits such as no pushing, draft-only, a named base, or no Linear. A request to open a PR includes the relevant commits and pushes. It does not authorize merging; use [auto-pilot-pr](../auto-pilot-pr/SKILL.md) when merging is authorized.

## Inspect the work

Read repository instructions. Inspect the remote, current branch, worktrees, staged and unstaged changes, untracked files, and commits ahead of the intended base. Verify GitHub access through an available connector or authenticated `gh`.

Resolve the actual base from the user's request, an existing PR, or the repository default branch. Fetch it before comparing committed work. Preserve a matching existing PR and its base. If a named base conflicts with that PR, resolve whether the work belongs in another PR before changing its target.

Preserve unrelated work. Reuse the correct feature branch; otherwise create a branch from the fetched base and transfer only relevant changes and commits. Prefer an isolated checkout when switching would disturb other work. Never blindly cherry-pick every ahead commit, indiscriminately stash or stage files, or force-push by default. Verify the head remote for fork PRs and respect push permissions.

If there are no relevant changes or commits, return the existing PR URL or report that there is nothing to submit.

## Choose the PR shape

Explicit user choices take precedence. Keep one coherent change together, including migrations and callers that must ship together. Split unrelated concerns into independent PRs. Stack dependent changes only when each layer builds and is safe to merge alone.

For a split or stack, show each PR's scope and base and obtain agreement unless the user already authorized that shape. Keep stacks shallow. A new child uses the current feature branch or named parent as its base, not the default branch. Record the parent's head before any rewrite. Every base must exist on the verified remote before opening its PR.

Process each PR once, bottom layer first. Reuse an existing matching PR rather than creating a duplicate.

## Resolve issue tracking and branch names

**No Linear:** when the user or their standing instructions excludes Linear, skip issue creation, Linear access checks, issue-writer, and Linear branch naming entirely. Missing Linear access never blocks this mode. Preserve supplied issue links without calling Linear. Keep the correct branch or choose a descriptive name following repository conventions.

Otherwise, preserve an existing issue. The team's default is one Linear issue per PR unless the user or repository selects another tracking policy. When a new Linear issue is needed, follow [issue-writer](../issue-writer/SKILL.md), create one per PR, and use its returned git branch name. Check Linear access and skill availability only in this mode. Link dependencies for a stack. Do not invent labels or project IDs.

## Validate and commit

Run the repository-required checks and focused verification of the changed behavior. Inspect the final diff and stage only relevant paths. Commit using repository conventions with hooks enabled. If a hook changes files, inspect and validate those changes before retrying. Do not amend an existing commit unless authorized.

FP Code supplies review after publication for repositories using it. Do not add a mandatory local reviewer, duplicate review report, or stamp request. Run extra reviews when the task or repository requires them.

## Capture UI evidence

When a PR changes what a user sees or does, read [screenshots.md](screenshots.md). Capture and inspect the affected views from the running app and attach them to the PR. Honor a request for no screenshots. If UI code has no visible effect, explain that briefly.

A capture or upload failure does not block independent PR work. Report the missing evidence. Refresh screenshots after later visible fixes.

## Publish and continue

Push to the verified feature branch. If auto-merge is already armed, disable it before pushing so an unverified head cannot merge.

Create or update the matching PR against its actual base, following its template. Use `gh pr create --base <base> --body-file <file>` or an equivalent connector. Describe the concrete problem, resulting behavior, and checks actually run. Include issue links only when present, screenshots for UI changes, and the parent and merge order for stacks. Preserve unrelated description content when updating.

Verify the URL, head, and base. When available, call `link_pull_request` immediately for each PR created or updated. Return every PR URL and show UI evidence in the final response.

Continue through [maintain-pr](../maintain-pr/SKILL.md), or [auto-pilot-pr](../auto-pilot-pr/SKILL.md) when merging is authorized. Do not run maintenance twice because skills compose. Report merged, ready, waiting, or blocked accurately.

## After a stack parent merges

Only advance children within the authorized task. Fetch the parent and new base, verify the child's remote head, and preserve unrelated work. Rebase the child with `git rebase --onto <new-base> <old-parent-head> <child>` when the parent's commits must be removed, including after a squash merge. Validate, push with an explicit `--force-with-lease=<branch>:<verified-remote-head>`, and retarget the child. Stop on concurrent changes or missing rewrite permission. Maintain and review the new head before it can merge.
