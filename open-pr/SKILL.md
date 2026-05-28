---
name: open-pr
description: Open a GitHub pull request from local changes by filing a Linear issue first, using Linear's git branch, committing, and creating the PR with gh. Use when the user asks to open a PR, create a pull request, ship changes, or submit work for review — including phrases like "open a PR", "create PR", or "put this up for review".
---

# Open Pull Request

Turn local work into a reviewable PR: analyze all changes, file a Linear issue, branch from Linear's suggested name, commit, and open a PR with `gh`.

## Prerequisites

- Run from the target git repository (not the skills repo unless that is the project).
- `gh` authenticated (`gh auth status`).
- Linear MCP available (plugin or user server).
- **issue-writer** skill available at `issue-writer/SKILL.md` in the skills install path, or bundled in this repo — read and follow it when creating the Linear issue.

Stop and tell the user what is missing if any prerequisite fails.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Analyze all local changes
- [ ] Step 2: Create Linear issue (issue-writer)
- [ ] Step 3: Checkout Linear git branch
- [ ] Step 4: Commit with descriptive message
- [ ] Step 5: Push and open PR with gh
```

### Step 1: Analyze all local changes

Resolve base branch first: default is the repo default branch (`gh repo view --json defaultBranchRef -q .defaultBranchRef.name`). Use a user-specified base branch when they name one (e.g. `develop`). Fetch it before comparing committed work: `git fetch origin <base>`.

Run in parallel:

```bash
git status
git diff
git diff --staged
git log -5 --oneline
git log origin/<base>..HEAD --oneline
```

Review **both** staged and unstaged diffs. Also check untracked files.

- **No changes** (clean tree, no untracked files, and no commits ahead of `origin/<base>`): stop — nothing to PR.
- **Scope too large** for one issue (~4+ hours or multiple unrelated concerns): follow issue-writer [splitting rules](../issue-writer/SKILL.md#splitting-large-work); do not proceed with a single PR until the user picks one slice.
- Note real file paths, patterns, and acceptance criteria — feed these into the Linear issue.

### Step 2: Create Linear issue

1. **Read** [issue-writer/SKILL.md](../issue-writer/SKILL.md) and follow its workflow (project, priority, labels from MCP, description template, required fields).
2. If issue-writer is not installed, apply the same rules inline: use the description template, fetch labels/projects via Linear MCP, never invent label names.
3. Derive issue content from Step 1 diffs — title in imperative mood, file paths and acceptance criteria from actual changes.
4. **Create** the issue via Linear MCP `save_issue` (pass `team`, `title`, `description`, `project`, `priority`, `labels`; use literal newlines in markdown, not `\n` escapes).
5. **Fetch branch name** via `get_issue` on the new issue id/identifier. Use the **git branch name** returned by Linear (e.g. `user/lin-123-short-title`). If absent, use Linear's branch naming convention for that team or ask the user.

Record the issue URL/identifier for the PR body.

### Step 3: Checkout Linear git branch

From the repo root. Use `<base>` from Step 1 (repo default or user-specified).

**Branch already exists locally** — switch to it (stash first only if checkout would fail):

```bash
git stash push -m "open-pr"    # only when dirty tree blocks checkout
git checkout <linear-branch-name>
git stash pop                  # only if you stashed
```

**Branch does not exist locally** — create it from the **base branch** tip, not current HEAD (stash first only if checkout would fail):

```bash
git fetch origin <base>
open_pr_ahead_commits="$(git rev-list --reverse origin/<base>..HEAD)"
git stash push -m "open-pr"    # only when dirty tree blocks checkout
git checkout -b <linear-branch-name> origin/<base>
if [ -n "$open_pr_ahead_commits" ]; then
  git cherry-pick $open_pr_ahead_commits
fi
git stash pop                  # only if you stashed
```

Record commits ahead of `origin/<base>` before checkout and cherry-pick them onto the Linear branch so committed local work is preserved. If you stashed dirty work, pop it after the cherry-pick so uncommitted changes are restored on top of the preserved commits.

If the branch exists on the remote but not locally: `git fetch origin <linear-branch-name> && git checkout -b <linear-branch-name> origin/<linear-branch-name>`.

- Do not use bare `git checkout -b <linear-branch-name>` without `origin/<base>` — that branches from whatever HEAD is on, which may not match the PR base.
- Do not force-checkout or discard unrelated user work without explicit approval.

### Step 4: Commit

Only commit when the user wants changes committed as part of this flow (default for "open a PR"). Follow git safety rules:

1. Run in parallel: `git status`, `git diff`, `git diff --staged`, `git log -5 --oneline`
2. Stage relevant files (not secrets: `.env`, credentials, etc.)
3. Draft a **1–2 sentence** commit message focused on **why**, matching recent repo style
4. Commit with a HEREDOC:

```bash
git add <paths>
git commit -m "$(cat <<'EOF'
<subject line>

<body if needed>
EOF
)"
```

- Never `--no-verify`, never amend unless user rules allow
- If hooks modify files, fix and make a **new** commit (do not amend a failed commit)

### Step 5: Push and open PR

```bash
git push -u origin HEAD
```

Then create the PR with `gh` against the base branch from Step 1:

```bash
gh pr create --base <base-branch> --title "<title aligned with Linear issue>" --body "$(cat <<'EOF'
## Summary
<1-3 bullets from the change>

## Linear
<issue URL or LIN-123 identifier>

## Test plan
- [ ] <how to verify>
EOF
)"
```

Return the PR URL to the user.

## Decision table

| Situation | Action |
|-----------|--------|
| User names a base branch | Use it for checkout source and `--base` |
| Linear branch already exists on remote only | `git fetch origin <linear-branch-name> && git checkout -b <linear-branch-name> origin/<linear-branch-name>` |
| Dirty tree blocks checkout | Stash, checkout, commit, then `git stash pop` if needed |
| Multiple unrelated change sets | Split per issue-writer; one PR per issue |
| User only wants PR, already committed on correct branch | Skip Steps 3–4 commit; still create/link Linear issue if missing |

## Anti-patterns

- Opening a PR without reading **both** staged and unstaged diffs
- Inventing Linear labels or skipping project/priority
- Using a hand-rolled branch name instead of Linear's `get_issue` branch
- `git checkout -b <branch>` without `origin/<base>` when creating a new branch
- `git push --force` to main/master
- Committing secret files

## Additional resources

- Linear issue quality: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Linear MCP: `save_issue`, `get_issue`, `list_projects`, `list_issue_labels`
