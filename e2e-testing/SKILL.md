---
name: e2e-testing
description: Implement tester-army's e2e library, build user-journey coverage, and integrate the suite into GitHub's merge queue without running E2E tests on every PR. Use when adopting this library, extending its tests, or wiring its CI gate.
---

# E2E testing

Build a runnable suite around the app's important user journeys using [tester-army/e2e](https://github.com/tester-army/e2e). Implement library setup, tests, and CI integration within the requested scope. Preserve an existing framework unless the user has chosen to adopt this library.

## Execution policy

The default CI policy is **E2E execution in the merge queue before main**. Ordinary PR opens and updates run the existing fast checks without executing E2E tests. Local runs and explicit manual dispatches remain available for development and diagnosis.

GitHub Actions queue execution uses `merge_group` with `checks_requested`, testing the event's combined commit. A `push` to main happens after merge and cannot provide this gate. Add post-deployment smoke tests only as a separate, requested capability.

Read [references/merge-queue.md](references/merge-queue.md) whenever adding or changing CI. It covers required-check coupling, the PR acknowledgement, environment identity, and verification.

## 1. Establish the application contract

Read repository guidance, package scripts and lockfile, existing tests, authentication, service dependencies, and workflows. Resolve:

- Target apps/platforms, production build/start commands, health checks, and runtime requirements.
- Existing framework and overlap with unit, integration, and manual QA coverage.
- Test accounts, roles, tenant boundaries, seed/reset APIs, and mutable external systems.
- How the exact queue commit will run, locally on the runner or in an isolated deployment.
- Branch rules, required check names, merge queue availability, and runner capabilities.

Prefer the existing package manager and lifecycle scripts. Keep E2E out of default unit-test globs and PR commands, including workspace-wide commands. A separate workflow does not help if `bun test` or another broad command still discovers these files.

Done when build, seed, execution commands, and CI events are explicit. Ask only for missing inputs that change implementation; continue independent work while waiting.

## 2. Install and configure the library

Use the installed version's guides as the API source of truth. Read `e2e guide setup` and `e2e guide writing-tests` through the project's package executor; read `e2e guide agent`, `running`, or `debugging` when using those capabilities. Before installation, use the [upstream references](https://github.com/tester-army/e2e/tree/main/skills/e2e/references). Verify current runtime requirements rather than copying an old Node version.

Install `e2e` and the relevant engine as development dependencies. Use `@e2e-dev/web` for browsers and `@e2e-dev/mobile` for mobile. Let the engine select its compatible underlying driver. Add an AI SDK provider only when tests use agent steps, choosing the project's approved model and CI authentication.

Create or extend `e2e.config.ts` as an ES module typed with `E2EConfig` from `e2e`. Declare targets with their engine and app. For web CI, prefer a production build and a runner-managed `app.command`; configure readiness and teardown. Set worker counts, timeouts, retry policy, and artifact retention for the suite's budget. Mobile targets also need a compatible runner/device, a build from the tested SHA, and reset/install steps from the installed guide.

Provide separate commands for running the suite and preparing dependencies. Preserve working configuration and avoid an initializer overwriting it. Keep credentials in the repository's secret system and use the library's `credentials` and `secrets` APIs. Commit neither account sessions nor secret values.

Done when a focused test reaches the running app with the installed CLI, and the commands work from the documented repository directory.

## 3. Build coverage from user journeys

Identify the highest-risk shipped flows from routes, requirements, and existing QA cases. Begin with a thin vertical slice through real UI, backend, and persistence. Extend to permission failures, validation errors, and relevant tenant boundaries. Record deferred journeys rather than claiming whole-app coverage.

Give each test a stable, descriptive identity, role, preconditions, expected outcomes, and tags when selection needs them. Seed data through a test API or fixture; keep the behavior under test in the UI. Make data unique per run and worker. Tests should pass independently and clean up their records after failure. Use isolated test services or sandboxes for payments, email, and other irreversible effects.

Learn the rendered accessible names before authoring locators. Use exact actions and retrying assertions for predictable interactions. Use `agent.act` for a meaningful goal, one goal per call, then immediately assert its observable outcome. A completed agent action alone is insufficient proof. Prefer exact assertions for prices, permissions, persisted state, and counts; reserve agent assertions for outcomes needing semantic judgment.

Import browser-typed tests and hooks from `@e2e-dev/web`, with `expect` from `e2e`; follow the installed guide for other fixtures. Reuse supported sign-in sessions for unrelated journeys while keeping dedicated login coverage. Use condition-based waits instead of fixed sleeps, and reload or revisit where persistence is the claimed outcome.

Run the focused test during development. Inspect its failure trace before changing a goal, locator, or assertion. Verify a new assertion detects an intentionally incorrect outcome, then restore the app/test. Re-run from clean seed data to expose order dependence.

Done when the selected journeys have meaningful assertions and have passed against the real app, with deferred coverage stated.

## 4. Make replay and failures explicit

For agent steps, verify a live run with `--no-cache` before relying on recordings. Inspect generated `.e2e/cache/` entries before committing approved recordings; never hand-edit them. Ignore generated reports, logs, results, and sessions separately so an ignore of all `.e2e/` does not silently exclude intended recordings.

Choose and document the CI mode. Strict replay uses `--strict-cache` to fail stale recordings, but unrecorded steps still run live. Live calls need approved provider authentication and explicit cost/time limits. Neither strict nor read-only cache guarantees zero model calls. If zero model calls are required, use deterministic steps or a verified runner policy that rejects all live execution; establish that behavior with a cache-miss check. Treat stale replay as test-maintenance failure, not a passing application result. Revalidate live when goals or relevant app behavior change.

Start with zero retries for the blocking suite so retry success does not hide instability. If the project chooses retries, report flaky results and define whether they block. Keep assertion failures, infrastructure failures, stale recordings, and incomplete runs distinguishable. Avoid `continue-on-error` on the gate.

If change-based selection is requested, retain a stable required core and report selected tests, rationale, and gaps. In fp-code integrations, keep selection decisions in fp-code rather than duplicating them as workflow path rules. Use the full agreed suite when selection is unavailable or invalid.

## 5. Wire and verify delivery

Apply the merge-queue reference and implement its app-specific preparation, test, and cleanup commands. Keep ordinary PR checks available on queue commits when required by the same branch rules.

Validate workflow syntax and discovery, run the suite from a clean environment, and verify event behavior. When live GitHub execution or settings access is unavailable, name the queue and branch-rule checks still unverified. Writing YAML is not proof the gate blocks a merge.

Finish with files changed, commands/outcomes, covered journeys, execution events, required check name, and remaining setup. Distinguish local success, CI success, branch-rule enforcement, and deployed acceptance. Stop once the requested suite and integration are implemented and available checks pass.
