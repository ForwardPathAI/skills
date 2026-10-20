---
name: pr-open
description: Open or reuse GitHub pull requests from local work, and decide whether it ships as one PR, several independent PRs, or a stack of dependent PRs. Also handles prepared branches supplied by release or security workflows. Use when submitting changes for review, splitting work into PRs, stacking a dependent PR on a branch, or when another skill needs PR creation.
---

# Open a pull request

Own the shared path from local changes to reviewable GitHub PRs. Callers own the feature, release, or security work and its verification requirements. This skill owns the PR shape, issue tracking when required, branch preparation, committing, pushing, and PR creation or reuse. Return to the caller after recording the PRs; merging and publishing belong to the caller.

## Inputs and defaults

These are workflow inputs, not CLI flags. Resolve them from the user request or calling skill before changing Git state.

| Input | Default and meaning |
|---|---|
| Repository | Current repository; verify the GitHub target and authenticated `gh` account. |
| Mode | `standard`; use `stacked` for a dependent PR, or `prepared` when the caller has already chosen and checked out the branch. |
| Shape | Decided in Step 2: one PR, a split into independent PRs, or a stack. A prepared branch or a caller's fixed batch is one PR. |
| Base | Repository default in standard/prepared mode; captured current branch in stacked mode. An explicit base overrides either default. |
| Tracking | `required`: reuse a matching Linear issue or create one. `none` is allowed only when the user or calling workflow explicitly selects it. |
| Issue | Existing issue ID/URL and branch name, if known. |
| Branch | Linear's returned branch for tracked work; caller-supplied branch in prepared mode. Otherwise follow repository branch conventions. |
| Existing PR | Optional URL/number. Verify its repository, head, base, and open state before updating. |
| Scope and evidence | Relevant paths, intended commits, and verification results. Preserve the caller's allowed-path restrictions and verification gates. |
| Content | Optional title, commit message, body sections, and existing labels. Keep caller-specific release notes, advisories, and dependency information. |

Require Linear MCP and [issue-writer](../issue-writer/SKILL.md) only for `tracking=required`. If a required skill is missing, resolve it from the available skill catalog or installed skill roots. Report the missing dependency rather than recreating its instructions from memory.

## 1. Inspect the intended change

Record the original branch, HEAD, and worktree status. Resolve the base before inspecting committed changes: a user-named base, otherwise the repository default (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`). Check that the base is on the remote (`git ls-remote --exit-code --heads origin <base>`). If it exists only locally, push it first, since every PR base must be on the remote; if it exists nowhere, stop and ask. Fetch it, and fetch the current branch only if it exists on the remote.

Check whether the current branch already has an open PR (`gh pr view --json number,url,state,baseRefName,headRefOid`). If it does, compare new work against that PR's head, not the base; its commits are not new work. If the user named a base, other than the current branch itself, that differs from that PR's `baseRefName`, stop and ask whether to retarget the PR or open a new branch and PR before you commit or push anything. Otherwise compare against the base.

Read staged, unstaged, and untracked work, recent commit style, and the commits and diff ahead of the compare point. Inspect the actual PR diff as well when reusing a PR. Note real paths, patterns, line counts, and acceptance criteria for the shape decision and the issues.

In stacked mode, capture the parent before creating the child. Commits already on that parent belong to the parent; only changes beyond it belong to the child. Read [branch handling](references/branches.md) before changing branches.

Identify the exact paths and commits that belong to this request. Leave unrelated work alone. If there is no work to submit, stop without creating an issue or branch; when the current branch has an open PR, return its URL. Preserve a caller's explicit batch boundary, such as one dependency ecosystem.

Check for an existing open PR for the intended head and base before creating anything. A supplied PR takes precedence after validation. An existing PR with a different base than the user named requires that same question. Do not silently retarget it or open another one.

Complete when scope, mode, base, tracking policy, and any existing issue/PR are known.

## 2. Choose the PR shape

Read [PR shape](references/shape.md) and pick one PR, a split, or a stack. Explicit user words win.

If the new work belongs in the current branch's open PR, do not open another one. Keep the current branch, satisfy tracking for that PR (Step 3), then commit, push, and update its body if the summary changed (Steps 4–5).

For a split or stack, show the user the plan — each PR's title, files, rough size, and base — and wait for approval before filing issues. Then run Steps 3–5 once per PR, bottom layer first:

- **Split:** each PR in `standard` mode on the default branch (or the user-named base).
- **Stack:** the bottom layer on its chosen base, then each next layer in `stacked` mode on the layer below it.

Complete when the shape, each PR's scope and base, and any required approval are settled.

## 3. Resolve issue tracking

Skip this step for `tracking=none`; do not require Linear or create an issue.

For `tracking=required`, use one issue per PR. Inspect the supplied issue, current branch, and existing PR (body and branch name) for an issue that actually covers this work. Reuse it rather than creating another. If none exists, call [issue-writer](../issue-writer/SKILL.md) in `create` mode with the inspected diff, repository evidence, and known team/project. That skill owns the Linear write and returns the issue ID, URL, and branch name. Do not repeat its create call here. When adding work to an open PR with no linked issue, create one this way and add it to that PR's body.

For a stack, set `blocked by` relations to match the stack order. For a split or stack of three or more PRs, ask issue-writer to group the issues in a Linear document per its [splitting](../issue-writer/splitting.md) rules.

Use the issue's branch name for new standard or stacked tracked work. Fetch it from Linear (`get_issue`) if needed; do not invent a replacement when the team's convention is unknown. A prepared branch stays as supplied by its caller. When updating a verified existing PR, preserve its head branch and reuse its associated issue instead of rebranching it.

Complete when the tracking policy is satisfied and the issue URL is available for the PR body, if required.

## 4. Prepare the branch and commit

Follow [branch handling](references/branches.md) for the selected mode. Once the target branch name is resolved, check for its existing open PR again if it differs from the branch inspected in Step 1. Verify the branch diff against the selected base contains the intended work and excludes unrelated commits.

Stage only the selected paths and review the staged diff, including anything that was already staged. Exclude unrelated staged work from the commit while preserving its content and restoring its prior staging afterward. Never include credential files. If unrelated changes share a file, stage the relevant hunks. Commit only when there are relevant uncommitted changes; preserve existing commits when no new commit is needed. Use the caller's commit message when supplied, otherwise match repository style and explain the change's purpose.

Run the repository's applicable checks, reusing results supplied by the caller when they still cover the current content. Honor stricter caller gates. In a stack, each layer must build and pass the checks on its own; run them before pushing that layer. Do not bypass hooks or amend existing commits by default. If hooks change files, inspect and verify them before retrying a failed commit or making a follow-up commit. Report any failures accurately.

Complete when the selected branch contains the intended changes, verification is recorded, and the caller's gates pass.

## 5. Push and create or reuse the PR

For a stacked PR, ensure the parent exists on the target remote at the intended parent tip before pushing the child. Push with ordinary non-force Git commands. If the remote has diverged, reconcile within the authorized scope or report the conflict; never overwrite it.

Compose the body from the actual diff and verification results. Include the Linear URL when tracking is required. For a stacked PR, add a "Stacked on" section naming the parent PR and branch, to merge first. Preserve supplied domain-specific sections. Distinguish completed checks from checks still pending.

Write the exact body to a temporary UTF-8 file. For a new PR:

```bash
git push -u origin HEAD
gh pr create --repo <owner/repo> --head <head-branch> --base <base-branch> \
  --title "<title>" --body-file <body-file>
```

Use the resolved remote if it is not `origin`. Add only labels that already exist. Before retrying an uncertain creation result, query for the head/base PR so a retry cannot create a duplicate.

For an existing open PR, push the relevant commits and return its URL. Update its title/body only when needed for this change, preserving unrelated reviewer content. Leave caller-specific comments to the caller. If it already describes the work and no changes are needed, return it without another write.

For a stack, once every layer is open, add the whole stack (bottom to top, with PR links) to each PR body so reviewers can see where each one sits. Report the merge order, bottom first. After a parent merges, the child needs its base updated; see [branch handling](references/branches.md#after-a-parent-merges).

When the host provides a PR attachment tool, attach each newly created PR to the current chat. Report every URL, head/base, issue URL if present, whether each PR was created or reused, and verification results. Return any blocker to the caller without claiming success. Use maintain-pr for ongoing upkeep.

## Anti-patterns

- Opening a PR without reading **both** staged and unstaged diffs.
- One giant PR mixing unrelated concerns — split it.
- Stacking layers that can't build or pass tests alone, or stacking deeper than ~3–4 PRs instead of slicing vertically.
- Splitting or stacking without showing the user the plan first.
- Cherry-picking a parent's commits onto a stacked branch.
- Basing a stacked PR on the default branch, or a split PR on another feature branch.
- Opening a PR whose base branch isn't on the remote.
- Using a hand-rolled branch name instead of Linear's branch for tracked work.
- Inventing Linear labels or skipping project/priority; issue-writer owns those fields.
- Force-pushing to the default branch, or committing secret files.
