---
name: stack-pr
description: Open a stacked GitHub pull request from local changes by filing a Linear issue first, branching off the CURRENT branch (not the repo default), committing, and creating the PR with gh against that branch as base. Use when the user wants to stack work on top of the branch they are on or chain dependent PRs — including phrases like "stack a PR", "stacked PR", "open a dependent PR", "stack this on top", or "branch on top of this".
---

# Stack Pull Request

Turn local work into a reviewable PR that **stacks on top of your current branch**: analyze the new changes, file a Linear issue, branch from the **current branch tip**, commit, and open a PR whose **base is the current branch**.

This is the sibling of [open-pr](../open-pr/SKILL.md). The only difference is the base:

| Skill | Base of the new branch / PR |
|-------|-----------------------------|
| open-pr | repo **default** branch (or a user-named base) |
| stack-pr | the **current** branch (or, when on the default branch, a base you pick) |

Everything else — Linear issue, branch from Linear's name, commit, `gh pr create` — is identical.

## Prerequisites

- Run from the target git repository (not the skills repo unless that is the project).
- `gh` authenticated (`gh auth status`).
- Linear MCP available (plugin or user server).
- **issue-writer** skill available at `issue-writer/SKILL.md` in the skills install path, or bundled in this repo — read and follow it when creating the Linear issue.
- The base branch (the branch you stack on) must be pushed to `origin` so the PR can target it. A PR base must exist on the remote.

Stop and tell the user what is missing if any prerequisite fails.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Resolve the base (stack parent) branch
- [ ] Step 2: Analyze new local changes
- [ ] Step 3: Create Linear issue (issue-writer)
- [ ] Step 4: Checkout Linear git branch off the base
- [ ] Step 5: Commit with descriptive message
- [ ] Step 6: Ensure base is on remote, push, and open PR with gh
```

### Step 1: Resolve the base (stack parent) branch

```bash
git rev-parse --abbrev-ref HEAD                              # current branch
gh repo view --json defaultBranchRef -q .defaultBranchRef.name   # default branch
```

Decide the base:

- **Current branch is NOT the default branch** → base = the current branch. This is what you stack on.
- **Current branch IS the default branch** (e.g. `main`/`master`) → stacking on the default is just a normal PR, so **ask the user which branch to base the work off of** before continuing. Offer the existing branches as options, or falling back to [open-pr](../open-pr/SKILL.md) (base off the default). Do not proceed until they answer.
- **User explicitly names a base branch** → use it (overrides the above).

Confirm the base exists on the remote: `git fetch origin <base>`. If it has no remote tracking branch yet, it will be pushed in Step 6 (a PR base must exist on `origin`).

### Step 2: Analyze new local changes

The stacked PR's diff is what is **new relative to the base**. When the base is your current branch (the common case), that is usually your uncommitted working-tree changes plus untracked files — commits already on the current branch belong to the **parent** and stay there.

Run in parallel:

```bash
git status
git diff
git diff --staged
git log -5 --oneline
git log <base>..HEAD --oneline       # commits on current branch not on base, if base != current
```

Review **both** staged and unstaged diffs. Also check untracked files.

- **No new changes** (clean tree, no untracked files, nothing to stack): stop — nothing to PR.
- **Scope too large** for one issue (~4+ hours or multiple unrelated concerns): follow issue-writer [splitting rules](../issue-writer/SKILL.md#splitting-large-work); do not proceed with a single PR until the user picks one slice.
- Note real file paths, patterns, and acceptance criteria — feed these into the Linear issue.

### Step 3: Create Linear issue

1. **Read** [issue-writer/SKILL.md](../issue-writer/SKILL.md) and follow its workflow (project, priority, labels from MCP, description template, required fields).
2. If issue-writer is not installed, apply the same rules inline: use the description template, fetch labels/projects via Linear MCP, never invent label names.
3. Derive issue content from Step 2 diffs — title in imperative mood, file paths and acceptance criteria from actual changes.
4. **Create** the issue via Linear MCP `save_issue` (pass `team`, `title`, `description`, `project`, `priority`, `labels`; use literal newlines in markdown, not `\n` escapes).
5. **Fetch branch name** via `get_issue` on the new issue id/identifier. Use the **git branch name** returned by Linear (e.g. `user/lin-123-short-title`). If absent, use Linear's branch naming convention for that team or ask the user.

Record the issue URL/identifier for the PR body.

### Step 4: Checkout Linear git branch off the base

Create the new branch from the **base tip** and carry your uncommitted work onto it.

**Base = current branch (common case)** — your working tree already sits on the base tip, so branch from HEAD; uncommitted changes follow automatically (stash first only if checkout would fail):

```bash
git checkout -b <linear-branch-name>
```

**Base = a different branch** (you were on the default branch, or named another base) — stash, branch off the base tip, pop:

```bash
git fetch origin <base>
git stash push -u -m "stack-pr"     # -u includes untracked; only when dirty tree blocks checkout
git checkout -b <linear-branch-name> origin/<base>
git stash pop                        # restore your new changes on top of the base
```

- Leave the parent branch's commits on the parent — **do not cherry-pick them onto the stacked branch**; the PR base already contains them.
- Do not use bare `git checkout -b <linear-branch-name>` without `origin/<base>` when the base is not the current branch — that branches from whatever HEAD is on, which may not match the PR base.
- If the branch already exists on the remote: `git fetch origin <linear-branch-name> && git checkout <linear-branch-name>`.
- Do not force-checkout or discard unrelated user work without explicit approval.

### Step 5: Commit

Only commit when the user wants changes committed as part of this flow (default for "stack a PR"). Follow git safety rules:

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

### Step 6: Ensure base is on remote, push, and open PR

If the base branch has no remote tracking branch yet, push it first so the PR can target it:

```bash
git push -u origin <base>     # only if <base> lacks a remote branch
```

Push the stacked branch and open the PR with the **parent as base**:

```bash
git push -u origin HEAD
```

```bash
gh pr create --base <base-parent-branch> --title "<title aligned with Linear issue>" --body "$(cat <<'EOF'
## Summary
<1-3 bullets from the change>

## Stacked on
Base branch `<base-parent-branch>` — merge that PR first.

## Linear
<issue URL or LIN-123 identifier>

## Test plan
- [ ] <how to verify>
EOF
)"
```

Return the PR URL to the user, note that it is stacked on `<base>`, and remind them the base PR should merge first.

## Decision table

| Situation | Action |
|-----------|--------|
| Current branch is a feature branch | base = current branch; PR `--base <current>` |
| Current branch is the default (`main`/`master`) | Ask which branch to stack on, or fall back to open-pr |
| User names a base branch | Use it for checkout source and `--base` |
| Base branch not yet on remote | `git push -u origin <base>` before `gh pr create` |
| Dirty tree, base = current branch | Branch from HEAD; changes carry over automatically |
| Dirty tree, base != current branch | `git stash push -u`, checkout off `origin/<base>`, `git stash pop` |
| New commits already on current branch | They belong to the parent — leave them; the PR base already has them |
| Multiple unrelated change sets | Split per issue-writer; one stacked PR per issue |

## Anti-patterns

- Basing the new branch/PR on the repo default when the user wants it stacked (that's [open-pr](../open-pr/SKILL.md))
- Cherry-picking the parent's commits onto the stacked branch (duplicates work; the base already contains them)
- Opening a stacked PR whose base branch isn't pushed to `origin`
- `git checkout -b <branch>` without `origin/<base>` when the base is not the current branch
- Opening a PR without reading **both** staged and unstaged diffs
- Inventing Linear labels or skipping project/priority
- Using a hand-rolled branch name instead of Linear's `get_issue` branch
- `git push --force` to main/master
- Committing secret files

## Additional resources

- Sibling skill (base = repo default): [open-pr/SKILL.md](../open-pr/SKILL.md)
- Linear issue quality: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Linear MCP: `save_issue`, `get_issue`, `list_projects`, `list_issue_labels`
