---
name: pr-open
description: Open or reuse a GitHub pull request from local work, including stacked PRs and prepared branches supplied by release or security workflows. Use when submitting changes for review or when another skill needs PR creation.
---

# Open a pull request

Own the shared path from local changes to a reviewable GitHub PR. Callers own the feature, release, or security work and its verification requirements. This skill owns issue tracking when required, branch preparation, committing, pushing, and PR creation or reuse. Return to the caller after recording the PR; merging and publishing belong to the caller.

## Inputs and defaults

These are workflow inputs, not CLI flags. Resolve them from the user request or calling skill before changing Git state.

| Input | Default and meaning |
|---|---|
| Repository | Current repository; verify the GitHub target and authenticated `gh` account. |
| Mode | `standard`; use `stacked` for a dependent PR, or `prepared` when the caller has already chosen and checked out the branch. |
| Base | Repository default in standard/prepared mode; captured current branch in stacked mode. An explicit base overrides either default. |
| Tracking | `required`: reuse a matching Linear issue or create one. `none` is allowed only when the user or calling workflow explicitly selects it. |
| Issue | Existing issue ID/URL and branch name, if known. |
| Branch | Linear's returned branch for tracked work; caller-supplied branch in prepared mode. Otherwise follow repository branch conventions. |
| Existing PR | Optional URL/number. Verify its repository, head, base, and open state before updating. |
| Scope and evidence | Relevant paths, intended commits, and verification results. Preserve the caller's allowed-path restrictions and verification gates. |
| Content | Optional title, commit message, body sections, and existing labels. Keep caller-specific release notes, advisories, and dependency information. |

Require Linear MCP and [issue-writer](../issue-writer/SKILL.md) only for `tracking=required`. If a required skill is missing, resolve it from the available skill catalog or installed skill roots. Report the missing dependency rather than recreating its instructions from memory.

## 1. Inspect the intended change

Record the original branch, HEAD, and worktree status. Resolve the base before inspecting committed changes. Read staged, unstaged, and untracked work, recent commit style, and the commits ahead of the selected base. Inspect the actual PR diff as well when reusing a PR.

In stacked mode, capture the parent before creating the child. Commits already on that parent belong to the parent; only changes beyond it belong to the child. Read [branch handling](references/branches.md) before changing branches.

Identify the exact paths and commits that belong to this request. Leave unrelated work alone. If there is no work to submit and no existing PR to report, stop without creating an issue or branch. For ordinary tracked work containing unrelated concerns, apply [issue-writer's splitting rules](../issue-writer/splitting.md) and select a coherent slice before proceeding. Preserve a caller's explicit batch boundary, such as one dependency ecosystem.

Check for an existing open PR for the intended head and base before creating anything. A supplied PR takes precedence after validation. An existing PR with a different base requires resolving that mismatch, not silently retargeting it or opening another one.

Complete when scope, mode, base, tracking policy, and any existing issue/PR are known.

## 2. Resolve issue tracking

Skip this step for `tracking=none`; do not require Linear or create an issue.

For `tracking=required`, inspect the supplied issue, current branch, and existing PR for an issue that actually covers this work. Reuse it rather than creating another. If none exists, call [issue-writer](../issue-writer/SKILL.md) in `create` mode with the inspected diff, repository evidence, and known team/project. That skill owns the Linear write and returns the issue ID, URL, and branch name. Do not repeat its create call here.

Use the issue's branch name for new standard or stacked tracked work. Fetch it from Linear if needed; do not invent a replacement when the team's convention is unknown. A prepared branch stays as supplied by its caller. When updating a verified existing PR, preserve its head branch and reuse its associated issue instead of rebranching it.

Complete when the tracking policy is satisfied and the issue URL is available for the PR body, if required.

## 3. Prepare the branch and commit

Follow [branch handling](references/branches.md) for the selected mode. Once the target branch name is resolved, check for its existing open PR again if it differs from the branch inspected in Step 1. Verify the branch diff against the selected base contains the intended work and excludes unrelated commits.

Stage only the selected paths and review the staged diff, including anything that was already staged. Exclude unrelated staged work from the commit while preserving its content and restoring its prior staging afterward. Never include credential files. If unrelated changes share a file, stage the relevant hunks. Commit only when there are relevant uncommitted changes; preserve existing commits when no new commit is needed. Use the caller's commit message when supplied, otherwise match repository style and explain the change's purpose.

Run the repository's applicable checks, reusing results supplied by the caller when they still cover the current content. Honor stricter caller gates. Do not bypass hooks or amend existing commits by default. If hooks change files, inspect and verify them before retrying a failed commit or making a follow-up commit. Report any failures accurately.

Complete when the selected branch contains the intended changes, verification is recorded, and the caller's gates pass.

## 4. Push and create or reuse the PR

For a stacked PR, ensure the parent exists on the target remote at the intended parent tip before pushing the child. Push with ordinary non-force Git commands. If the remote has diverged, reconcile within the authorized scope or report the conflict; never overwrite it.

Compose the body from the actual diff and verification results. Include the Linear URL when tracking is required and the parent branch/PR for stacked work. Preserve supplied domain-specific sections. Distinguish completed checks from checks still pending.

Write the exact body to a temporary UTF-8 file. For a new PR:

```bash
git push -u origin HEAD
gh pr create --repo <owner/repo> --head <head-branch> --base <base-branch> \
  --title "<title>" --body-file <body-file>
```

Use the resolved remote if it is not `origin`. Add only labels that already exist. Before retrying an uncertain creation result, query for the head/base PR so a retry cannot create a duplicate.

For an existing open PR, push the relevant commits and return its URL. Update its title/body only when needed for this change, preserving unrelated reviewer content. Leave caller-specific comments to the caller. If it already describes the work and no changes are needed, return it without another write.

When the host provides a PR attachment tool, attach a newly created PR to the current chat. Report the URL, head/base, issue URL if present, whether the PR was created or reused, and verification results. Return any blocker to the caller without claiming success.
