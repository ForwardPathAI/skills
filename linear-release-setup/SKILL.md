---
name: linear-release-setup
description: Set up GitHub Release workflows that publish containers and sync scheduled Linear Releases.
disable-model-invocation: true
---

# Linear Release Setup

Set up the repo so Linear's scheduled production release is the customer-facing release record: pushes to `main` feed the current in-progress release, then a published production GitHub Release finishes it after release artifacts ship.

Reference implementation: `PRS-Walmart-PRIME` uses `.github/workflows/linear-release-main.yml` for main-branch sync and `.github/workflows/release.yml` for GitHub Release sync + complete. Copyable workflow templates live in [WORKFLOWS.md](WORKFLOWS.md).

## Wrapped Release Work

If the repo does not already build and publish release containers, first use [azure-infra-setup](../azure-infra-setup/SKILL.md) to understand or create the Azure container publishing path. Return here once a published GitHub Release can produce the customer release artifacts; this skill adds the Linear scheduled-release layer around that release.

## Discovery

1. Read `.github/workflows/` and deployment docs. Finish when you know which workflow publishes customer release artifacts, whether it runs on `release.published`, and whether it distinguishes prereleases.
2. Match the repo's workflow style: runner labels, checkout version, action pinning policy, image build action, and summary conventions. Do not churn unrelated CI.
3. Confirm the Linear setup: a scheduled release pipeline exists in Linear, its pipeline access key is stored as `LINEAR_ACCESS_KEY`, and path filters are configured when the repo is a monorepo. A personal Linear API key is not a substitute for the pipeline access key.
4. Check that merged PRs/commits preserve Linear issue keys such as `ENG-123`; Linear can only attach issues it can discover from the commit range.

## Implementation

1. Add `.github/workflows/linear-release-main.yml` to sync every push to `main` into the current scheduled Linear release. Use `fetch-depth: 0`, `LINEAR_ACCESS_KEY`, no `command`, and no `version`.
2. In the GitHub Release workflow, add a Linear job after release artifacts build and publish successfully. Checkout the release tag with full history, then sync the release with `name: ${{ github.event.release.tag_name }}` and links to the GitHub Release plus CI run.
3. Complete only production releases. Prereleases should sync and attach links, but must leave the Linear release in progress.
4. Share a concurrency group such as `linear-release-sync` between all jobs that touch the same Linear pipeline. Use `cancel-in-progress: false` so a main push cannot race or cancel a release completion.
5. For scheduled production pipelines, do not pass `version` unless the user intentionally wants a separate versioned release model. PRIME completes the latest started release by omitting `version` and passing the GitHub tag as `name`.
6. If multiple Linear release pipelines are needed, use separate access-key secrets and separate concurrency groups per pipeline.

## Verification

1. Run the repo's workflow validation, usually `actionlint` for changed workflow files.
2. Parse changed YAML with an existing repo tool if available; do not add a dependency only for validation.
3. Confirm the final release workflow cannot complete Linear when image publishing fails.
4. Confirm the final release workflow leaves prereleases in progress.
5. Do not publish a real GitHub Release as a test unless the user explicitly asks.

## Handoff

Report the changed workflow files, the exact secret name required, whether Linear path filters still need to be configured, and the validation commands/results. If GitHub release publishing was not already present and could not be created, say that the Linear setup is blocked on the wrapped release work.
