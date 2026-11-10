# Merge queue integration

## Event and required-check contract

GitHub couples PR and merge queue required checks through the target branch's protection rules or ruleset. A required E2E check emitted only on `merge_group` can leave PRs waiting before they can enter the queue.

Use one stable gate name, such as `E2E gate`, with these behaviors:

- `pull_request` targeting main: report success with an explicit acknowledgement that E2E execution is deferred to the queue. Skip dependency installation, app startup, credentials, and tests.
- `merge_group` with `checks_requested` targeting main: prepare and test the exact combined commit. Succeed only after the agreed suite passes.
- `workflow_dispatch`: run the suite for diagnosis on the selected ref. This does not replace a queue result.

This is a workflow run on every PR, but **no E2E tests run on ordinary PR events**. Make that distinction visible in the log and runbook. Main must require the merge queue and the stable gate, with bypass permissions understood, or the acknowledgement could allow untested direct merges.

Inspect effective rules before changing settings. Use existing authorization for in-scope changes; if access is unavailable, supply the exact configuration as a remaining setup item. Authored workflow files are not proof of enabled enforcement.

See GitHub's [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue) for required-check coupling and the separate `merge_group` event.

## Workflow shape

Adapt this web example to the repository. It uses Bun for package scripts and Node for the library runtime. Resolve action versions against the repository's pinning policy and current runtime requirements. Size the timeout from measured startup and suite duration.

Implement these project scripts before using it:

- `e2e:prepare`: build the app, provision isolated dependencies, migrate/seed, and install the engine's matching browser and OS dependencies. Configure startup under `app.command`. A deployed target instead provisions the exact tested SHA and verifies readiness and build identity.
- `test:e2e:ci`: run the installed library with explicit policy, reports, and failure propagation. A strict replay suite might use `e2e run --strict-cache --retries 0 --reporter list,junit`. Strict mode rejects stale recordings but still runs unrecorded steps live, so account for provider authentication and budget. Verify cache-miss behavior rather than promising zero model calls. Fail if no required tests run or required coverage is unexpectedly skipped; validate the installed report schema if a wrapper enforces this.
- `e2e:cleanup`: delete only resources owned by this run, handling partial setup safely.

Inject only environment variables the scripts/config actually read. Model credentials are needed for live agent calls, including unrecorded steps under strict cache mode. Scope secrets to execution steps or an appropriate test environment, leaving the PR acknowledgement without them.

Expose credentials only to queued changes the repository trusts. Code from the combined queue commit can read secrets available to its execution steps; step scoping does not protect credentials from that code. For queues admitting untrusted changes, use a secret-free suite or require explicit trusted approval before credentialed execution, with disposable, narrowly scoped credentials. Apply the same trust requirement to manual dispatches on a selected ref.

```yaml
name: E2E
on:
  pull_request:
    branches: [main]
  merge_group:
    types: [checks_requested]
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: e2e-${{ github.event_name }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  e2e:
    name: E2E gate
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Defer PR E2E execution to the merge queue
        if: github.event_name == 'pull_request'
        run: echo 'E2E tests execute when this PR enters the merge queue.'

      - uses: actions/checkout@v4
        if: github.event_name != 'pull_request'
        with:
          persist-credentials: false

      - uses: actions/setup-node@v4
        if: github.event_name != 'pull_request'
        with:
          node-version: '24.8.0'

      - uses: oven-sh/setup-bun@v2
        if: github.event_name != 'pull_request'
        with:
          bun-version-file: package.json

      - name: Install dependencies
        if: github.event_name != 'pull_request'
        run: bun install --frozen-lockfile

      - name: Prepare test application
        id: prepare
        if: github.event_name != 'pull_request'
        run: bun run e2e:prepare

      - name: Run E2E suite
        if: github.event_name != 'pull_request'
        run: bun run test:e2e:ci

      - name: Retain diagnostic artifacts
        if: ${{ always() && github.event_name != 'pull_request' && steps.prepare.outcome != 'skipped' }}
        uses: actions/upload-artifact@v4
        with:
          name: e2e-${{ github.sha }}-${{ github.run_attempt }}
          path: |
            .e2e/report.json
            .e2e/junit.xml
            .e2e/results/
          include-hidden-files: true
          if-no-files-found: error
          retention-days: 7

      - name: Clean up test resources
        if: ${{ always() && github.event_name != 'pull_request' && steps.prepare.outcome != 'skipped' }}
        run: bun run e2e:cleanup
```

Checkout defaults to the triggering event's ref/SHA. Preserve that checkout for merge groups. Overriding it with the PR head or current main tests different code. Propagate `github.sha` through any handed-off build artifact/image and verify the running build before testing.

The example versions demonstrate structure. Select supported patches and immutable action SHAs during implementation. Use the repository's pinned Bun version; `bun-version-file` assumes its package metadata declares one. Adapt paths and working directories for monorepos. Configure test secrets/environment before claiming it is runnable.

For shards, retain one stable final gate that runs even when dependencies fail. It must inspect every required shard and fail on failure, cancellation, or unexpected skip. Dependency propagation must not silently skip the gate and approve the queue.

## Environment and failure handling

Prefer a runner-local app with disposable services when the whole stack fits. Otherwise key deployments, data, and accounts by queue SHA plus run ID and attempt. A PR preview is insufficient unless it runs the same combined commit and its identity is verified. Shared mutable staging can validate another run's code or data.

Retain sanitized reports and failure evidence, including traces/screenshots where produced. Avoid uploading sessions, credentials, or unrestricted service logs. Preserve nonzero test status through reporting and cleanup. Cancellation or runner termination can prevent cleanup, so external resources also need expiration or a janitor.

Scope concurrency to the queue ref, rather than one global group that cancels unrelated candidates. Superseded runs must clean up only their resources. Match the queue status timeout to the workflow budget plus runner startup margin.

Keep the workflow unfiltered by paths so its required check always appears. Audit other required lint, typecheck, build, and unit jobs for `merge_group` support. Event-specific steps make the PR acknowledgement explicit without relying on skipped-job semantics.

## Acceptance checks

1. PR open/update produces `E2E gate` without installing dependencies, starting the app, or invoking tests. Existing fast checks still run.
2. Queue entry produces the same gate on the merge group's SHA. Record tested build identity and expected test count.
3. A controlled assertion failure on a disposable test branch blocks the queue and retains evidence. A healthy run permits merging after other required checks pass.
4. Missing configuration, startup failure, stale strict replay, and no runnable required tests fail visibly. No success fallback masks them.
5. A newer commit or reformed group receives a new run. Concurrent candidates stay isolated; cancellation/partial setup do not leak long-lived resources.
6. Manual dispatch runs on its selected ref. A push to main does not duplicate the full suite by default.

If GitHub execution is unavailable, validate syntax/scripts locally and report these as pending live checks. If the GitHub plan does not support merge queues, name the limitation. A post-merge run or another pre-merge gate needs an explicit policy choice and does not silently satisfy the queue requirement.

## Library reference

Read installed `e2e guide running` for current flags, CI defaults, browser installation, and report fields. The [upstream running guide](https://github.com/tester-army/e2e/blob/main/skills/e2e/references/running.md) supplies library mechanics; replace its PR/push execution triggers with this skill's policy.
