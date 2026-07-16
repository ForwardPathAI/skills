---
name: release
description: Cut a production GitHub release from the default branch with gh — semver tag, release notes, breaking-change gate, and CI watch. SDK repos (publishable package.json) get a version-bump release PR before tagging.
disable-model-invocation: true
---

# Release

Cut a **production** GitHub release from the repo's **default branch**: scan for customer-breaking changes, propose a semver tag, compose release notes from commits and linked tracker issues, publish with `gh`, and watch the release-triggered workflow until it succeeds.

Works in any git repo — discover branch names, tag format, CI workflows, and release pipelines from the repo; do not assume monorepo layout, container registry, or a specific issue tracker prefix.

Two **release modes**, detected in Step 1:

- **App mode** — tag the default branch directly (Steps 1–7 as written).
- **SDK mode** — the repo publishes a package whose publish workflow requires the tag to match `package.json` version, so a version-bump release PR must merge before tagging. Steps 5–6 are replaced by [SDK-RELEASE.md](./SDK-RELEASE.md).

Production only — no prerelease tags or `--prerelease` flows.

## Prerequisites

Run from the target application repo (not the skills folder).

| Requirement | Check |
|-------------|-------|
| `gh` authenticated | `gh auth status` |
| Remote default branch | `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` |
| At least one prior release (recommended) | `gh release list --limit 1` — if none, ask the user for the starting tag/version |

Linear MCP is **optional** — use it to enrich release notes when commit messages contain issue identifiers the MCP can resolve.

Stop and tell the user what is missing before Step 1.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Pre-flight
- [ ] Step 2: Breaking-change gate (stop until user approves)
- [ ] Step 3: Semver + version confirm
- [ ] Step 4: Compose release notes
- [ ] Step 5: Publish release
- [ ] Step 6: Watch release workflow
- [ ] Step 7: Done report
```

### Step 1: Pre-flight

**Completion criterion:** `origin/<default-branch>` is fetched, local branch matches it, there is at least one commit since the last production tag, the latest CI run on that branch is not failed, and the release mode is recorded.

Set variables from the repo:

```bash
DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)"
git fetch origin "$DEFAULT_BRANCH"
git checkout "$DEFAULT_BRANCH"
git pull --ff-only origin "$DEFAULT_BRANCH"
git rev-parse HEAD "origin/$DEFAULT_BRANCH"   # must match
LAST_TAG="$(gh release list --limit 1 --exclude-pre-releases --json tagName -q '.[0].tagName // empty')"
if [ -n "$LAST_TAG" ]; then
  git log "${LAST_TAG}..origin/$DEFAULT_BRANCH" --oneline
fi
```

- **No prior release:** ask the user for `LAST_TAG` or the commit to release from.
- **No commits** since `LAST_TAG`: stop — nothing to release.
- **Local branch behind/ahead** of remote: stop — sync first.

Infer **tag prefix** from `LAST_TAG` (e.g. `v` in `v1.2.3`, or none). Reuse the same prefix for the new tag.

**CI on default branch** — discover the workflow; do not assume a filename:

```bash
gh workflow list --json name,path
gh run list --branch="$DEFAULT_BRANCH" --limit 10 --json workflowName,conclusion,status,url,event
```

Pick the most recent run on `$DEFAULT_BRANCH` for a push/merge CI workflow (skip `release`-event runs). If `conclusion` is `failure`, stop and show the run URL. If `status` is `in_progress` or `queued`, tell the user and wait (`gh run watch <id>`) or ask whether to proceed.

**Release mode** — SDK mode when the root `package.json` has `publishConfig` (or the release workflow runs `npm publish` / verifies tag against `package.json` version); app mode otherwise. Confirm with the user when the signals conflict.

Record `LAST_TAG`, `DEFAULT_BRANCH`, tag prefix, and release mode for all later steps.

### Step 2: Breaking-change gate

**Completion criterion:** every applicable scan in [BREAKING-CHANGE-SCAN.md](./BREAKING-CHANGE-SCAN.md) is run for paths that exist in this repo, findings are presented, and the user explicitly approves proceeding (or aborts).

This step runs **before** semver or release notes. Do not skip or merge with later steps.

1. Read [BREAKING-CHANGE-SCAN.md](./BREAKING-CHANGE-SCAN.md) and run scans for `${LAST_TAG}..origin/$DEFAULT_BRANCH` — skip paths that do not exist in the repo.
2. Present findings in a table: **Category | Path/signal | Summary | Deployment impact**.
3. If any finding exists, flag that **customer/deployment documentation** (env vars, infra, secrets, runbooks) may need updating. Do not auto-run other skills unless the user asks.
4. Use **AskQuestion** (or equivalent explicit confirmation): *Proceed with release despite these findings?* Options: **Proceed** / **Abort**.

On **Abort**, stop. On **Proceed** (including zero findings), continue.

### Step 3: Semver + version confirm

**Completion criterion:** user confirms the exact tag string before any `gh release create`.

Parse `LAST_TAG` (strip inferred prefix) into major, minor, patch using semver semantics.

**Default bump:** patch (`v1.2.3` → `v1.2.4`). Apply patch unless the user specifies minor or major.

| User says | Bump |
|---------|------|
| (nothing) | patch |
| minor / feature release | minor |
| major / breaking | major |

Match the new tag to the repo's existing convention (prefix + `X.Y.Z`). If the repo enforces a tag format in CI, read the release workflow file and respect it.

Present: last tag, proposed tag, bump rationale, commit count since last tag. Ask the user to confirm the tag or name a different version. Do not publish until confirmed.

### Step 4: Compose release notes

**Completion criterion:** release notes body is ready, includes a compare link, and every commit in the release range appears once (directly or via its PR).

Gather commits:

```bash
git log "${LAST_TAG}..origin/$DEFAULT_BRANCH" --pretty=format:"%h %s" --reverse
```

For each commit, resolve the merged PR when present:

```bash
gh pr list --state merged --search "<sha>" --json number,title,url --limit 1
```

Extract issue identifiers from commit subjects (common patterns: `ABC-123`, `LIN-456`, `#789`). Collect unique IDs. When Linear MCP (or another tracker MCP) is available, fetch titles and use them in note lines.

Group lines under:

- **Features** — `feat`, user-facing work
- **Fixes** — `fix`, bug fixes
- **Chores** — everything else, **including Dependabot** (`chore(deps)`, `@dependabot`)

Match the style of the repo's previous release when one exists (`gh release view "$LAST_TAG" --json body -q .body`).

Format each line:

```markdown
* <title or commit subject> by @<author> in <PR URL>
```

Author from `gh pr view <num> --json author -q .author.login` when a PR exists; otherwise from `git log --format=%an`.

Append:

```markdown
**Full Changelog**: https://github.com/<owner>/<repo>/compare/<LAST_TAG>...<NEW_TAG>
```

Use `gh repo view --json nameWithOwner -q .nameWithOwner` for owner/repo.

Show the full notes body to the user before Step 5.

### Step 5: Publish release

**SDK mode:** follow [SDK-RELEASE.md](./SDK-RELEASE.md) for Steps 5–6 (release PR → merge → tag → watch), then return to Step 7. The rest of this step and Step 6 are app mode.

**Completion criterion:** GitHub release exists, is **published** (not draft), tag targets the default branch.

Discover whether publish triggers CI from workflow files:

```bash
gh workflow list
# Read workflows under .github/workflows/ whose `on.release.types` includes `published`
```

```bash
gh release create <NEW_TAG> \
  --target "$DEFAULT_BRANCH" \
  --title "<NEW_TAG>" \
  --notes "$(cat <<'EOF'
<release notes body>
EOF
)"
```

- Do **not** pass `--draft` when a release workflow expects `published`.
- Do **not** pass `--prerelease` — production only.
- Return the release URL from `gh release view <NEW_TAG> --json url -q .url`.

### Step 6: Watch release workflow

**Completion criterion:** every job in the release-triggered workflow run completed with `conclusion: success`, or the user confirms there is no release workflow to watch.

**Discover** the workflow — do not assume a filename or job names:

```bash
# List workflows; read files with `on: release:` / `types: [published]`
gh workflow list --json name,path
```

If one or more release workflows exist, find the run triggered by this publish (retry up to ~2 minutes if not listed yet):

```bash
gh run list --event=release --limit 10 --json databaseId,headBranch,conclusion,status,url,createdAt,workflowName
```

Pick the run matching `<NEW_TAG>` or the release timestamp. Then:

```bash
gh run watch <run-id> --exit-status
gh run view <run-id> --json conclusion,url,jobs --jq '.jobs[] | {name, conclusion}'
```

- On **failure** or **cancelled**: report the run URL, list failed jobs, and stop — do not treat Step 7 as complete.
- On **success**: continue.
- **No release workflow** in the repo: tell the user publish is complete and skip watch after confirming with them.

### Step 7: Done report

**Completion criterion:** user receives tag, release URL, workflow status, and deployment handoff flag if Step 2 had findings.

Report:

| Item | Source |
|------|--------|
| Tag / release URL | Step 5 |
| Workflow run URL(s) | Step 6 (if any) |
| Workflow job summary | All jobs and conclusions from Step 6 |
| Deployment handoff | Repeat Step 2 findings if any; note that env/infra/docs may need a customer update |

Summarize artifact outputs (container images, npm packages, etc.) only from what the release workflow actually did — read the workflow file or job logs; do not invent registry URLs or service names.

## Decision table

| Situation | Action |
|-----------|--------|
| Default branch is not `main` | Use `$DEFAULT_BRANCH` everywhere — never hardcode `main` |
| No prior releases | Ask user for baseline tag or first version |
| User names a different tag | Use their version after format validation |
| User requests minor/major bump | Apply that bump instead of default patch |
| CI still running | Wait or ask — do not silently skip |
| Breaking-change findings | Present all, ask, abort on decline |
| No release workflow in repo | Skip Step 6 watch after user acknowledgment |
| SDK mode (publishable package.json) | Replace Steps 5–6 with [SDK-RELEASE.md](./SDK-RELEASE.md) |
| Workflow not found immediately | Poll `gh run list` briefly before failing |
| Release workflow failed | Report failure; do not claim release is complete |

## Anti-patterns

- Assuming repo layout (monorepo paths, specific Dockerfiles, migration folders, ACR URLs)
- Publishing before the breaking-change gate approval
- Draft releases when CI expects `published`
- Prerelease tags or `--prerelease`
- Skipping workflow watch when a release pipeline exists
- Omitting Dependabot commits from notes
- Inventing tracker issue titles without MCP lookup
- Treating a failed release workflow as a successful release
- Tagging an SDK repo before the version-bump PR is merged (publish fails on tag/version mismatch)

## Additional resources

- Breaking-change scan paths and semver rules: [BREAKING-CHANGE-SCAN.md](./BREAKING-CHANGE-SCAN.md)
- SDK release PR flow (Steps 5–6 replacement): [SDK-RELEASE.md](./SDK-RELEASE.md)
