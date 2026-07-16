# SDK release: version-bump PR flow

Replaces **Steps 5–6** of [SKILL.md](./SKILL.md) when the repo is in **SDK mode**. Steps 1–4 (pre-flight, breaking-change gate, semver confirm, release notes) run unchanged first. Return to Step 7 when done.

Why this flow exists: SDK publish workflows require the tag to match `package.json` version (whether they trigger on tag push or on `release: published`). The version bump must therefore land on the default branch — via a release PR — **before** the tag is created.

## Step 5a: Release PR

**Completion criterion:** `package.json` version on `origin/$DEFAULT_BRANCH` equals the confirmed version (tag minus prefix), landed via a merged PR (PR checks passed when any exist).

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

- Wait for PR checks when any exist: `gh pr checks --watch`. If the PR reports no checks (common when CI only runs on the default branch), proceed. On check failure, stop and report.
- Merge using the repo's convention (check merged-PR history; default `gh pr merge --squash --delete-branch`).
- Re-sync and verify:

```bash
git checkout "$DEFAULT_BRANCH" && git pull --ff-only origin "$DEFAULT_BRANCH"
node -p "require('./package.json').version"   # must equal <X.Y.Z>
```

Refresh the Step 4 notes for `${LAST_TAG}..HEAD` so every commit now on the default branch appears once — including any that landed while PR checks ran. Place the bump PR under **Chores**.

## Step 5b: Tag + publish release

**Completion criterion:** GitHub release published; tag points at the default-branch head that contains the version bump; local `package.json` version equals the tag.

Same `gh release create` command as Step 5 in SKILL.md, targeting the post-merge `$DEFAULT_BRANCH` head (use the refreshed notes body). Creating the release (and its tag) is what triggers the publish workflow.

## Step 6 (SDK): Watch publish workflow

**Completion criterion:** the publish workflow run for this release completed with `conclusion: success`.

Discover the publish workflow — do not assume a filename or trigger event. Read `.github/workflows/` for files that run `npm publish` (or equivalent package publish) and note their `on:` trigger:

- `on: push: tags:` → event is `push`; a run's `headBranch` is the tag name
- `on: release: types: [published]` → event is `release` (same pattern as app-mode Step 6)

```bash
gh workflow list --json name,path
# Read the publish workflow file(s); record workflow name and event (push vs release)
gh run list --event=<push|release> --limit 10 --json databaseId,headBranch,status,conclusion,url,workflowName
# Pick the run where workflowName matches the publish workflow AND headBranch/tag matches <NEW_TAG>
# (or release timestamp matches); retry ~2 min if not listed yet
# Do not pick a generic tag/CI run that does not publish
gh run watch <run-id> --exit-status
```

On failure: report the run URL and failed jobs, and note the recovery order — the version bump is already merged, so fix the workflow and re-run or delete and re-push the tag; do **not** merge another bump PR for the same version.

Package URL for the Step 7 report: read the package name from `package.json` (e.g. `https://www.npmjs.com/package/<name>`), but only claim it published from the run's job logs.
