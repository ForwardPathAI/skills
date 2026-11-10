# CI naming and reporting contract

Apply this contract when creating or changing GitHub Actions jobs and work steps. Preserve existing triggers and merge requirements unless their migration is in scope.

## Canonical stages

- `lint`: linting, formatting, and style checks. Display `Lint` or `Lint / <target>`.
- `typecheck`: an explicit compiler/type-analysis check. Display `Typecheck` or `Typecheck / <target>`.
- `test`: executable tests. Display `Test / <suite>` or `Test / <suite> / <target>`; use `unit`, `integration`, or `e2e` where verified. Describe other suites with stable lowercase slugs. Keep combined suites explicit.
- `build`: compile, bundle, package, or build a container image. Display `Build` or `Build / <target>`. Typechecking inherent in compilation remains part of build; record a separate typecheck measurement only when it runs separately.
- `security`: dependency, vulnerability, secret, or code-security scans. Display `Security` or `Security / <target>`.
- `deploy`: apply infrastructure or deploy/promote an artifact. Display `Deploy / <environment>` or `Deploy / <environment> / <target>`.
- `release`: version, publish, or update a release record. Display `Release` or `Release / <target>`.
- `automation`: orchestration, dependency updates, reports, metadata checks, telemetry, and aggregate gates. Use `Automation / <purpose>`. Required aggregate checks may retain names such as `Validation gate` or `E2E gate`; classify their acknowledgements as automation.
- `mixed`: an existing job explicitly combines multiple stages. Use `Checks / mixed / <target>` for a new bundled job when separate jobs would add unnecessary setup cost. Give each distinct work step its canonical stage prefix.
- `unknown`: insufficient evidence or an unreviewed identity. Keep it visible for reporting follow-up; this is not a name for a new job.

Trace commands and package scripts before assigning a stage. `check`, `checking`, `verify`, and `App Checks` carry no typecheck guarantee. A gate that reads dependency results is automation. A job that explicitly builds and deploys is mixed. Shared installation, caching, and cleanup remain job overhead, not independent validation stages.

Prefer separate single-stage jobs when setup cost permits. For a bundled job, use steps such as `Lint / web`, `Typecheck / web`, `Test / unit / web`, and `Build / web`. Step durations may then support stage metrics; assigning the entire job duration to each of those stages would multiply the same time.

## Stable identities and dimensions

Use lowercase kebab-case job IDs such as `lint`, `typecheck-web`, and `test-e2e`. Display names use the spelling above. Keep workflow names stable and descriptive, for example `CI`, `Deploy / dev`, or `Release`.

Represent these independently in a repository's reporting map or existing event emitter:

- `stage`, `target`, and `suite`: use stable component slugs such as `web`, `api`, or `workspace`; use `unknown` when unresolved and `not_applicable` where the dimension does not apply.
- `validation_scope`: `full`, `affected`, `affected_or_full`, `not_applicable`, or `unknown`. A change-based selector with a full fallback is `affected_or_full` until execution evidence identifies the branch actually taken.
- `trigger_event`: preserve GitHub's event name. Distinguish PR, merge-queue, main-branch, manual, and scheduled lanes. Event names alone do not establish affected/full scope.
- `environment`: use the repository's GitHub environment identity; preserve `production` even where Azure resource names use `prod`.
- Raw repository, workflow path/name, job ID/name, step name/number, run ID, job ID, attempt, head SHA, status, conclusion, and timestamps: retain these for attribution and debugging.

An existing reporting mechanism is sufficient. Add no PostHog credential or collector merely to comply with naming. A legacy alias belongs in a reviewed mapping keyed by repository, workflow identity, and job identity, with command evidence and a mapping version. If those names have changed meaning, constrain by commit/version or observed step signature; new or changed definitions fall back to unknown.

Keep compiler and test matrices explicit. Add only stable dimensions to names, for example `Test / unit / api (linux)`. Keep commit SHAs, PR numbers, dates, and attempt numbers in metadata. Third-party or GitHub-managed workflow names may be normalized in the reporting map without editing their source.

## Required-check migration and verification

Before renaming an existing job, inspect branch protections/rulesets, `needs`, reusable-workflow check names, matrices, dashboards, and reporting aliases. Preserve the old required check until its replacement reports on every required event and branch rules reference the replacement. Scope a rename separately if access or evidence is missing.

For each changed job, verify:

1. Commands, called actions/workflows, and package scripts agree with its assigned stage and dimensions. Bundled work and gate-only acknowledgements remain distinguishable.
2. Display names, job IDs, matrix dimensions, and work-step names follow this contract. Review the executed steps when live runs are available.
3. PR build-only and full queue validation still follow the CI skill's execution policy. A PR acknowledgement contributes no test execution or test-duration sample.
4. Required-check names, dependencies, and aliases still resolve. Run the repository's workflow validator and changed commands; report unavailable live/ruleset checks separately.
5. Reporting counts a job once per job identity/attempt and a step once per job identity/attempt/step number. Preserve cancelled, skipped, failed, and unfinished outcomes. Successful-duration percentiles exclude failed/cancelled samples; rates exclude non-decisive outcomes and carry their denominator.

Job duration includes preparation and cleanup. Sum of parallel job durations is runner work, not pipeline wall-clock latency. Compare like stages, targets, suites, scopes, and lanes, and surface unknown/mixed coverage beside the trend.
