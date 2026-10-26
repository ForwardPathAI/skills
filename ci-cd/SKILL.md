---
name: ci-cd
description: Configure or review GitHub Actions pipelines with PR builds and full validation in the merge queue. Use when setting up CI/CD or changing event triggers and required checks.
---

# CI/CD

## Execution policy

- `pull_request` on opens, updates, and reopens: build only. Compiler checks inherent in the build stay; separate validation runs in the queue.
- `merge_group` with `checks_requested`: build, lint, check formatting, type-check, and run unit, integration, E2E, and existing project-specific checks against the combined queue commit.
- Deployment and release: preserve existing triggers unless the request includes changing them. Post-merge checks cannot gate a merge.

## Apply

1. Inspect workflows, called actions/workflows, package scripts, and effective branch rules. Map every existing check to its event and command. Trace build/install hooks for hidden validation so deferred suites do not still run on PRs.
2. Relocate checks without losing coverage. Use existing tools and commands; report missing suites as gaps. Build and test the event SHA, including any deployed E2E target, rather than a PR preview or latest main.
3. Wire the required checks using the enforcement contract below. Preserve existing protections until the replacement works. If queue availability or settings access blocks enforcement, report the exact remaining setup.
4. Validate workflow syntax and changed commands. Verify PR build-only behavior, full queue execution, failure propagation, and effective queue rules. Separate static validation from observed GitHub runs and live enforcement in the report.

## Enforcement contract

GitHub couples PR and queue required checks through branch rules. Use stable names, retaining existing names where practical:

- `Build` runs on both events and requires a successful build.
- `Validation gate` acknowledges deferred validation on PRs; on queue commits it requires every mandatory validation job to succeed.

Require both checks and the merge queue on target branches. Inspect bypass permissions. The PR acknowledgement is safe only when direct merges cannot bypass queue validation. Queue-only required names can prevent PRs entering the queue.

The aggregate gate must run after failed or cancelled dependencies, for example with `if: always()`, and explicitly check each mandatory result for `success`. Unexpected skips, missing jobs, cancellation, and failures must never produce a successful queue gate. Keep failures blocking.

Required checks must report without path-filter gaps or duplicate names. Separate PR and queue concurrency groups so unrelated queue commits cannot cancel each other's checks. Keep deployment tied to the actual merged or released SHA.

Consult [GitHub's merge queue documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) when implementing branch-rule or event behavior.
