# SDK release: version-bump PR flow

Replaces **Steps 5–6** of [SKILL.md](./SKILL.md) when the repo is in **SDK mode**. Steps 1–4 (pre-flight, breaking-change gate, semver confirm, release notes) run unchanged first. Return to Step 7 when done.

Why this flow exists: SDK publish workflows trigger on **tag push** (`on: push: tags:`) and fail hard when the tag does not match `package.json` version. The version bump must therefore land on the default branch — via a release PR — **before** the tag is created.

## Step 5a: Release PR

**Completion criterion:** `package.json` version on `origin/$DEFAULT_BRANCH` equals the confirmed version (tag minus prefix), landed via a merged PR whose CI passed.

```bash
git checkout -b "release/<NEW_TAG>" "origin/$DEFAULT_BRANCH"
npm pkg set version="<X.Y.Z>"          # version without tag prefix
```

- **Lockfile:** run the repo's install (`bun install`, `npm install`, …) and commit the lockfile if it changed — some lockfiles embed the root version.
- Commit as `chore: release <NEW_TAG>`, push, open the PR:

```bash
git push -u origin "release/<NEW_TAG>"
gh pr create --title "chore: release <NEW_TAG>" --body "Version bump for <NEW_TAG>. Release notes preview below.

<Step 4 notes body>"
```

- Wait for PR checks: `gh pr checks --watch`. On failure, stop and report.
- Merge using the repo's convention (check merged-PR history; default `gh pr merge --squash --delete-branch`).
- Re-sync and verify:

```bash
git checkout "$DEFAULT_BRANCH" && git pull --ff-only origin "$DEFAULT_BRANCH"
node -p "require('./package.json').version"   # must equal <X.Y.Z>
```

Append the release PR itself to the Step 4 notes under **Chores** — it is now part of the release range.

## Step 5b: Tag + publish release

**Completion criterion:** GitHub release published; tag points at the default-branch head that contains the version bump; local `package.json` version equals the tag.

Same `gh release create` command as Step 5 in SKILL.md, targeting the post-merge `$DEFAULT_BRANCH` head. The tag push this creates is what triggers the publish workflow.

## Step 6 (SDK): Watch publish workflow

**Completion criterion:** the tag-push-triggered publish run completed with `conclusion: success`.

The workflow event is `push` (tag), not `release` — a run's `headBranch` is the tag name:

```bash
gh run list --event=push --limit 10 --json databaseId,headBranch,status,conclusion,url,workflowName
# pick the run where headBranch == <NEW_TAG>; retry ~2 min if not listed yet
gh run watch <run-id> --exit-status
```

On failure: report the run URL and failed jobs, and note the recovery order — the version bump is already merged, so fix the workflow and re-run or delete and re-push the tag; do **not** merge another bump PR for the same version.

Package URL for the Step 7 report: read the package name from `package.json` (e.g. `https://www.npmjs.com/package/<name>`), but only claim it published from the run's job logs.
