---
name: open-pr
description: Open GitHub pull requests from local changes by filing a Linear issue first, using Linear's git branch, committing, and creating the PR with gh. Decides whether the work ships as one PR, several independent PRs, or a stack of dependent PRs. Use when the user asks to open a PR, ship changes, or put work up for review — including "stack a PR", "stacked PR", "open a dependent PR", "stack this on top", "split this into PRs", or "branch on top of this".
---

# Open Pull Request

Turn local work into reviewable PRs: analyze all changes, decide the PR shape (one, split, or stacked), then for each PR file a Linear issue, branch from Linear's suggested name, commit, and open the PR with `gh`.

## Prerequisites

- Run from the target git repository (not the skills repo unless that is the project).
- `gh` authenticated (`gh auth status`).
- Linear MCP available (plugin or user server).
- **issue-writer** skill available at `issue-writer/SKILL.md` in the skills install path, or bundled in this repo — read and follow it when creating Linear issues.

Stop and tell the user what is missing if any prerequisite fails.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Analyze all local changes
- [ ] Step 2: Choose PR shape (one / split / stack) and base
- [ ] Step 3: Create Linear issue(s) (issue-writer)
- [ ] Step 4: Checkout Linear git branch
- [ ] Step 5: Commit with descriptive message
- [ ] Step 6: Push and open PR with gh
```

For a split or a stack, run Steps 4–6 once per PR, bottom layer first.

If the work is already committed on the correct Linear branch and the user only wants the PR, skip Steps 4–5 — but still create and link a Linear issue (Step 3) if one is missing.

### Step 1: Analyze all local changes

Resolve the repo default branch: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. Note the current branch: `git rev-parse --abbrev-ref HEAD`. Fetch both before comparing: `git fetch origin <default> <current>`.

Run in parallel:

```bash
git status
git diff
git diff --staged
git log -5 --oneline
git log origin/<default>..HEAD --oneline
git diff --stat origin/<default>...HEAD
```

Review **both** staged and unstaged diffs. Also check untracked files.

- **No changes** (clean tree, no untracked files, and no commits ahead of `origin/<default>`): stop — nothing to PR.
- If the current branch already has an open PR (`gh pr view --json number,state,baseRefName`), the new work is either more of that PR or a stack on top of it. Decide in Step 2.
- Note real file paths, patterns, line counts, and acceptance criteria — feed these into Step 2 and the Linear issues.

### Step 2: Choose PR shape and base

Pick one shape. Explicit user words win ("stack this" → stack; "one PR" → one PR).

| Shape | Use when | Base |
|-------|----------|------|
| **One PR** | One concern, a reviewer can read it in one sitting, or the parts only make sense together | default branch (or user-named base) |
| **Split** (independent PRs) | Two or more concerns with no dependency between them (a feature plus an unrelated fix or drive-by refactor) | each PR on the default branch |
| **Stack** (dependent PRs) | Parts must land in order, and the whole is too big for one review | each PR on the PR below it |

**Keep it as one PR when:**

- It is under ~400 changed lines of hand-written code (ignore lockfiles, generated code, snapshots, fixtures).
- The parts would break `main` if merged alone (a rename and all its callers; a migration and the code that requires it in the same deploy).
- Splitting would add more review overhead than it saves (tiny prep commits, one-line fixes).

**Split into independent PRs when:**

- The diff mixes unrelated concerns. Each concern gets its own PR, issue, and branch off the default branch.
- Pieces can merge in any order. If one piece needs another, that is a stack, not a split.

**Stack when all of these hold:**

- The work is over ~400 lines or spans several layers, and one reviewer pass would be hard.
- The pieces depend on each other in a clear order. Common layers, bottom to top:
  1. Prep refactor or mechanical change (rename, move, format) — no behavior change
  2. Schema, migration, or shared types
  3. Backend / API
  4. UI / client
- Each layer builds, passes tests, and is safe to merge alone. The bottom layer must be shippable to `main` without the layers above it.
- The user wants review to start before the whole feature is done, or is adding new work on top of a branch whose PR is still open.

**Don't stack when:**

- A layer can't build or pass tests without the one above it — merge those layers or reorder.
- The stack would go deeper than ~3–4 PRs. Rebases get painful; split by vertical slice instead (see issue-writer [splitting](../issue-writer/splitting.md)).
- The parent PR is likely to churn a lot in review. Wait for it to settle, or keep the work in one PR.

**Base rules for a stack:**

- On a feature branch and stacking new work on top → base = current branch.
- On the default branch and the user asks to stack → ask which branch to stack on, or fall back to one PR on the default branch. Do not proceed until they answer.
- User names a base → use it.
- The base must exist on `origin`. Push it first if it has no remote branch.

**Confirm before splitting.** For one PR, proceed. For a split or stack, show the user the plan — each PR's title, files, rough size, and base — and wait for approval before filing issues.

### Step 3: Create Linear issue(s)

One issue per PR.

1. **Read** [issue-writer/SKILL.md](../issue-writer/SKILL.md) and follow its workflow (project, priority, labels from MCP, description template, required fields).
2. If issue-writer is not installed, apply the same rules inline: use the description template, fetch labels/projects via Linear MCP, never invent label names.
3. Derive issue content from the Step 1 diffs — title in imperative mood, file paths and acceptance criteria from actual changes.
4. **Create** each issue via Linear MCP `save_issue` (pass `team`, `title`, `description`, `project`, `priority`, `labels`; use literal newlines in markdown, not `\n` escapes).
5. For a stack, set `blocked by` relations to match the stack order. For a split or stack of three or more, group the issues in a Linear document per issue-writer [splitting](../issue-writer/splitting.md).
6. **Fetch branch name** via `get_issue` on each new issue id/identifier. Use the **git branch name** returned by Linear (e.g. `user/lin-123-short-title`). If absent, use Linear's branch naming convention for that team or ask the user.

Record each issue URL/identifier for its PR body.

### Step 4: Checkout Linear git branch

From the repo root. `<base>` is the base chosen in Step 2.

**Branch already exists locally** — switch to it (stash first only if checkout would fail):

```bash
git stash push -u -m "open-pr"    # only when dirty tree blocks checkout
git checkout <linear-branch-name>
git stash pop                     # only if you stashed
```

**Branch exists on the remote only** — `git fetch origin <linear-branch-name> && git checkout -b <linear-branch-name> origin/<linear-branch-name>`.

**New branch, base = current branch** (stacking on the branch you are on, or the next layer of a stack you are building) — branch from HEAD; uncommitted changes carry over:

```bash
git checkout -b <linear-branch-name>
```

Leave the parent's commits on the parent. Do not cherry-pick them; the PR base already has them.

**New branch, base = another branch** (default branch, or a named base) — branch from the **base tip**, not current HEAD, and carry over commits that are ahead (stash first only if checkout would fail):

```bash
git fetch origin <base>
open_pr_ahead_commits="$(git rev-list --reverse origin/<base>..HEAD)"
git stash push -u -m "open-pr"    # only when dirty tree blocks checkout
git checkout -b <linear-branch-name> origin/<base>
if [ -n "$open_pr_ahead_commits" ]; then
  git cherry-pick $open_pr_ahead_commits
fi
git stash pop                     # only if you stashed
```

Only cherry-pick ahead commits that belong in this PR. If you are on a feature branch whose commits belong to its own open PR, you are stacking — use the branch-from-HEAD case instead.

- Do not use bare `git checkout -b <linear-branch-name>` when the base is not the current branch — that branches from whatever HEAD is on, which may not match the PR base.
- Do not force-checkout or discard unrelated user work without explicit approval.

**Building a split or stack from one pile of changes:** work one PR at a time. Check out its branch, stage only that PR's files or hunks (`git add <paths>` or `git add -p`), commit (Step 5), push and open the PR (Step 6). The remaining uncommitted changes stay in the working tree. For a stack, branch the next layer from HEAD. For a split, branch the next PR from `origin/<default>`, stashing the rest across the checkout if needed.

### Step 5: Commit

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
- In a stack, each layer must build and pass the repo's checks on its own. Run them before pushing the layer.

### Step 6: Push and open PR

If the base has no remote branch yet, push it first: `git push -u origin <base>`.

```bash
git push -u origin HEAD
```

Then create the PR with `gh` against `<base>`:

```bash
gh pr create --base <base> --title "<title aligned with Linear issue>" --body "$(cat <<'EOF'
## Summary
<1-3 bullets from the change>

## Stacked on
<stacked PRs only: #<parent PR> (`<base>`) — merge that first. Omit this section otherwise.>

## Linear
<issue URL or LIN-123 identifier>

## Test plan
- [ ] <how to verify>
EOF
)"
```

For a stack, once all layers are open, add a short list of the whole stack (bottom to top, with PR links) to each PR body via `gh pr edit` so reviewers can see where each one sits.

Return every PR URL to the user. For a stack, give the merge order (bottom first). After a parent merges, rebase the child onto the new base and retarget it (`gh pr edit <child> --base <new-base>`); with squash merges use `git rebase --onto origin/<new-base> <old-parent-tip>`. Use maintain-pr for ongoing upkeep.

## Anti-patterns

- Opening a PR without reading **both** staged and unstaged diffs
- One giant PR mixing unrelated concerns — split it
- Stacking layers that can't build or pass tests alone
- Stacking deeper than ~3–4 PRs instead of slicing vertically
- Splitting or stacking without showing the user the plan first
- Cherry-picking a parent's commits onto a stacked branch
- Basing a stacked PR on the default branch, or a split PR on another feature branch
- Opening a PR whose base branch isn't on `origin`
- Inventing Linear labels or skipping project/priority
- Using a hand-rolled branch name instead of Linear's `get_issue` branch
- `git push --force` to main/master
- Committing secret files

## Additional resources

- Linear issue quality: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Splitting work into issues: [issue-writer/splitting.md](../issue-writer/splitting.md)
- Linear MCP: `save_issue`, `get_issue`, `list_projects`, `list_issue_labels`
