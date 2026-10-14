---
name: security-sweep
description: Sweep a GitHub org for open Dependabot alerts and open one grouped fix PR per repo per ecosystem, skipping alerts an existing PR already covers. Use when the user asks to fix vulnerable dependencies across all repos, clear an org's Dependabot backlog, or run a security sweep.
---

# Security Sweep

One pass over every active repo in a GitHub org: read open Dependabot alerts, drop the ones an open PR already covers, collapse the rest into one **batch** per repo per ecosystem, fix each batch locally, and open the PR.

The sweep is **autonomous** — no confirmation between scan and push. Invoking it is the authorization. What keeps that safe is Step 4: a batch only becomes a PR after the install resolves every patched version and the repo's own checks pass.

Dependabot alerts only. Code scanning and secret scanning are out of scope — a leaked secret needs rotation and history scrubbing, not a PR.

## Prerequisites

- `gh` authenticated with repo write access to the org (`gh auth status`). If `/dependabot/alerts` returns 403 for *every* repo, the token is missing a scope: `gh auth refresh -h github.com -s security_events`.
- `jq`.
- Toolchains for the ecosystems in play (bun/pnpm/npm, uv/poetry, go, dotnet, cargo…). A missing toolchain fails its batch — record it and sweep on; never hand-edit a lockfile to work around it.
- Org name. Default **ForwardPathAI** when the user doesn't name one.

Stop and tell the user what is missing if a prerequisite fails.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Scan the org
- [ ] Step 2: Order the sweep
- [ ] Step 3: Fix one batch          (repeat per batch)
- [ ] Step 4: Verify the batch       (repeat per batch)
- [ ] Step 5: Push and open the PR   (repeat per batch)
- [ ] Step 6: Report the sweep
```

Steps 3–5 run per batch, one batch at a time, start to finish before the next. Never leave a half-fixed clone behind to come back to.

### Step 1: Scan the org

```bash
SWEEP=$(mktemp -d)
./scan.sh <ORG> "$SWEEP/plan.json"
```

The script is read-only: it lists active repos (not archived, not a fork, not empty), pulls open Dependabot alerts and open PRs per repo in parallel, and writes the plan. It also prints a summary — read it before doing anything else.

What the plan already decided, so you don't re-decide it:

| Field | Meaning |
|-------|---------|
| `batches[]` | The work. One per repo per ecosystem, sorted by severity. |
| `batches[].fixes[]` | One entry per package, with `target` = highest patched version across that package's alerts. **This is the dedupe** — 20 alerts for `next` across 9 manifests is one bump. |
| `batches[].existing_sweep_pr` | A previous sweep's open PR for this ecosystem. Add commits to it; do not open a second. |
| `batches[].verify_against_prs` | Grouped Dependabot PRs ("Bump the npm_and_yarn group with 3 updates") that name no package. Read their diffs before fixing — they may already cover part of the batch. |
| `covered[]` | Alerts an open PR already fixes. Skip them silently; they belong in the report only. |
| `no_fix[]` | Alerts with no patched version. No PR is possible. Report them. |
| `repos_unreadable[]` | Alerts API errored (disabled, or no permission). Report them — an unreadable repo is not a clean repo. |

**Done when** every repo the script scanned lands in exactly one bucket: has batches, clean, unreadable, or its alerts are all in `covered`/`no_fix`. Reconcile the counts against `repos_scanned` before moving on.

### Step 2: Order the sweep

Take `batches` in plan order (severity first). Then apply one split:

**A major-version bump gets its own batch.** Compare `target` against the version in the manifest after cloning. A major jump can break the build, and batching it with safe patches means one breakage buries five good fixes. Split it onto its own branch — `security-sweep-major/<ecosystem>-<pkg>-<date>`, a different prefix so a later sweep never appends safe bumps to it — and mark the PR title `[breaking risk]`.

Rails for the whole sweep:

- Only ever create or push branches named `security-sweep/*` or `security-sweep-major/*`. Never touch another branch, never force-push, never rebase someone's work.
- The diff may contain manifests, lockfiles, and lock artifacts (`go.sum`, `Cargo.lock`, `packages.lock.json`) only. If a tool regenerated anything else, `git checkout --` it before committing.
- Never commit a credential file the install wrote (`.npmrc`, `.env`, `auth.json`).
- If the install needs a private-registry token you don't have, the batch is needs-human. Do not disable integrity checks or `--force` past it.
- Installing dependencies runs their lifecycle scripts. That is inherent to producing a real lockfile; it is the repo's own dependency tree, not new code.

### Step 3: Fix one batch

```bash
git clone --depth 1 --filter=blob:none "https://github.com/<ORG>/<REPO>.git" "$SWEEP/<REPO>"
cd "$SWEEP/<REPO>"
git checkout -b "security-sweep/<ecosystem>-$(date -u +%Y%m%d)"
```

When `existing_sweep_pr` is set, check that branch out instead (`git fetch origin <branch> && git checkout <branch>`) and add to it.

Then, per fix in the batch, read [ECOSYSTEMS.md](ECOSYSTEMS.md) for the ecosystem's detect/bump/verify commands and apply them. The plan's `manifests` tells you where the package is declared; a package in none of them is transitive — ECOSYSTEMS.md has the fallback ladder (lockfile bump, then an override pin).

Do all bumps for the batch, then install **once**.

**Done when** every fix in the batch has been applied or explicitly recorded as skipped with a reason.

### Step 4: Verify the batch

Three gates, all required:

1. Install exits 0 and the lockfile changed.
2. **Every** fix's resolved version is `>= target` — check with the ecosystem's resolution query (`pnpm why`, `npm ls --all`, `go list -m all`, `dotnet list package --include-transitive`…). A bumped manifest with a stale lockfile resolution fixes nothing.
3. The repo's own checks pass: its declared typecheck/lint/build/test scripts, whichever exist. Skip the ones the repo doesn't define; don't invent commands.

On failure: drop the offending package from the batch, reinstall, retry once. Still failing → drop the whole batch to needs-human with the first ~20 lines of the error, and open no PR. A red PR across 30 repos is worse than no PR.

**Done when** all three gates pass for the packages that remain, and every dropped package is recorded.

### Step 5: Submit the verified batch

Read and follow [pr-open](../pr-open/SKILL.md) with this handoff:

| Input | Value |
|---|---|
| Mode / tracking | `prepared` / `none`; this sweep does not require Linear. |
| Repository / base | The batch's repository and its default branch. |
| Branch / existing PR | The checked-out `security-sweep/*` or `security-sweep-major/*` branch, plus `existing_sweep_pr` when present. |
| Allowed paths | Only the batch's manifests, lockfiles, and lock artifacts. |
| Verification | Step 4 results, including package-resolution evidence and any documented pre-existing baseline failure. |
| Title / commit message | `fix(deps): patch <N> vulnerable <ecosystem> dependencies`; retain `[breaking risk]` in the title for major-version batches. |
| Labels | `security` only if it already exists in that repository. |

Supply these PR body sections, populated from the verified batch:

```markdown
## Dependabot alerts closed by this PR

| Package | From | To | Severity | Advisory |
|---------|------|----|----------|----------|
| <package> | <old> | <resolved> | <severity> | <GHSA reference> |

<N> alerts, deduped to <M> package bumps.

## Verification
- Install: <command and result>
- Resolution: <query and result for every patched package>
- Repository checks: <commands and results>

Opened by security-sweep.
```

pr-open owns committing, pushing, and creating or reusing the PR. Do not run a second PR creation procedure here. When it reuses `existing_sweep_pr`, add a comment with the newly fixed rows and verification results after the push succeeds; check for an existing matching comment before retrying.

**Done when** the returned PR URL is recorded, or the batch is recorded as needs-human with its blocker. Then clean up the sweep-owned clone and move to the next batch.

### Step 6: Report the sweep

One table, **every** repo the scan touched on a row — no silent drops:

```
Security sweep — <ORG>, <date>

| Repo | Ecosystem | Alerts | Outcome |
|------|-----------|--------|---------|
| SentrexHub | npm | 86 → 6 bumps | PR #412 |
| PRS-RAG | pip | 2 | already covered by #176 |
| fp-os | — | 0 | clean |
| legacy-api | npm | 4 | needs human: pnpm install fails on private registry |
| old-tool | — | ? | unreadable: alerts disabled |

Opened <N> PRs closing <M> alerts. <K> repos need a human.
```

Then say plainly what a human still owes: needs-human batches, `no_fix` alerts, unreadable repos, and any `[breaking risk]` PR.

## Decision table

| Situation | Action |
|-----------|--------|
| Alert package is not in any manifest | Transitive — lockfile bump, then override pin (ECOSYSTEMS.md). |
| `target` is a major jump | Its own batch, own branch, PR title marked `[breaking risk]`. |
| Grouped Dependabot PR open in the repo | Read its diff first; drop anything it already bumps. |
| A previous sweep's PR is open for that ecosystem | Add commits to it; never open a second. |
| Alert has no patched version | Report only. No PR exists that could fix it. |
| Repo's tests were already failing on the default branch | Compare against a baseline run before the bump; if red before, don't block the PR on it — say so in the PR body. |
| Toolchain for the ecosystem is missing locally | Batch → needs-human. Never hand-edit lockfiles. |
| User names one repo | Run the scan with `REPOS="<repo>"`; the rest is unchanged. |

## Anti-patterns

- Opening one PR per alert. 86 alerts for one package across nine workspaces is **one** bump.
- Trusting a bumped manifest without checking the resolved version — the lockfile decides what ships.
- Committing when the install failed, "so a human can finish it." That is what needs-human in the report is for.
- Deep-cloning every repo in the org. Shallow, blobless, one at a time, deleted after.
- Reporting only the PRs you opened. Unreadable repos and no-fix alerts are the part a human has to act on.
- Re-deriving dedupe or PR coverage by hand — `scan.sh` did both; read the plan.

## Additional resources

- Per-ecosystem bump, transitive-fallback, and verification commands: [ECOSYSTEMS.md](ECOSYSTEMS.md)
- Enumeration script (read-only, runnable standalone): [scan.sh](scan.sh) — `./scan.sh --help`
