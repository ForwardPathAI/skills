# Engineering

Skills we use for Forward Path engineering and delivery work.

## User-invoked

Reachable only when you type them (`disable-model-invocation: true`).

- **[release](./release/SKILL.md)**: Cut a production GitHub release from the default branch — semver tag, release notes, breaking-change gate, and CI watch.
- **[auto-pilot-pr](./auto-pilot-pr/SKILL.md)**: Run maintain-pr until the latest head is ready, then arm GitHub auto-merge on it. Disarms before each of its own pushes, so its unverified heads never merge. Install with `maintain-pr`.
- **[execute](./execute/SKILL.md)**: Run one ticket (Linear issue, GitHub issue, or improve plan) or a whole spec of tickets through to PRs that have merged or are armed to merge: executor subagents build each ticket in a worktree, the lead agent reviews each diff, then runs code-review, simplify, open-pr, and auto-pilot-pr. A spec runs its ticket graph frontier by frontier. Install with `open-pr`, `issue-writer`, `maintain-pr`, and `auto-pilot-pr`.
- **[ticket-refiner](./ticket-refiner/SKILL.md)**: Interview the person who knows why a Linear ticket exists and rewrite it to pass issue-writer's agent-ready bar.
- **[qa-test-plan-setup](./qa-test-plan-setup/SKILL.md)**: Per-project one-time creation of a `<Project> — QA Test Plan` Notion database with the fixed Forward Path schema (test case, feature, steps, expected result, category, priority, status).
- **[linear-release-setup](./linear-release-setup/SKILL.md)**: Set up GitHub Release workflows that publish containers, keep a scheduled Linear release in progress from main merges, and complete it when the customer GitHub Release ships.

## Model-invoked

The model can reach for these on its own; you can also call them by name.

- **[issue-writer](./issue-writer/SKILL.md)**: Write Linear issues an AI coding agent can execute without follow-up questions — scoped by behavior, not file lists — or turn a feature into a spec document and tracer-bullet tickets with native blocking relations.
- **[open-pr](./open-pr/SKILL.md)**: Open GitHub PRs from local changes via a Linear issue, Linear's git branch, commit, and `gh` — decide whether to ship one PR, split it, or stack dependent PRs, and attach verified screenshots when the diff changes UI.
- **[maintain-pr](./maintain-pr/SKILL.md)**: Maintain an open GitHub PR through human and independent review-agent feedback, merge conflicts, and CI failures — triage findings, fix, validate, push, reply/resolve, and recheck the latest head until it is ready or concretely blocked.
- **[code-review](./code-review/SKILL.md)**: Review a working-tree diff, branch, or specified PR for evidence-backed correctness bugs and regressions.
- **[security-review](./security-review/SKILL.md)**: Review a working-tree diff, branch, or specified PR for vulnerabilities with verified attack paths and severity.
- **[azure-conventions](./azure-conventions/SKILL.md)**: Forward Path Azure conventions — resource naming, environments, regions, Container Apps, shared ACR, OIDC/RBAC, Key Vault, and known gotchas.
- **[azure-ops](./azure-ops/SKILL.md)**: Inspect and operate live Azure apps with the `az` CLI — locate resources, stream and query logs, check revisions, images, identities, and secrets, and follow symptom playbooks for failed deploys, 5xx errors, and database or Key Vault failures.
- **[infisical](./infisical/SKILL.md)**: Forward Path's app and CI/CD secrets rules — Infisical as the single source of truth, no local `.env` files, and Secret Syncs into GitHub and Azure Key Vault.
- **[mobile-ui](./mobile-ui/SKILL.md)**: Turn a SOW into a grounded Expo SDK 54 screen spec and premium portrait UI mockups (via Google Gemini or OpenRouter, with a consent-gated on-device Apple-Silicon fallback when no cloud key is available).
- **[mobile-ui-implement](./mobile-ui-implement/SKILL.md)**: Turn mobile UI mockups (PNG screens or a PDF deck) into per-screen implementation blueprints, then build them in an Expo Go-compatible app — decomposing each screen into layers, components, states, and animations a weaker model can build one at a time.
- **[web-ui](./web-ui/SKILL.md)**: Turn a SOW and/or a real Next.js + Tailwind codebase into a grounded web screen spec and consistent desktop mockups (via Google Gemini or OpenRouter, with a consent-gated on-device Apple-Silicon fallback when no cloud key is available) — anchored by a brand style board and a persistent app-shell (nav/sidebar) so every screen looks like one credible product.
- **[customer-deployment-package](./customer-deployment-package/SKILL.md)**: Build a customer-facing deployment handoff — external Terraform/Bicep, setup instructions filled into the Notion template and saved to the deployments DB, then exported and zipped with a Windows-safe name.
- **[qa-test-plan](./qa-test-plan/SKILL.md)**: Add QA test cases to the Notion QA Test Plan database — generate candidates from a feature change or the whole app, get QA approval, then append rows QA works through during full regression runs.
- **[teach-web-actions](./teach-web-actions/SKILL.md)**: Learn a website by recording a user-driven Chrome session (HAR + UI steps) via Playwright codegen, distill it into a reusable lesson (endpoints, payloads, parameter knobs, auth), then replay a variation with new parameters as an API call or as UI navigation captured to mp4.
- **[product-foundation](./product-foundation/SKILL.md)**: The standard stack and conventions for building Forward Path products — Bun monorepo, Next.js App Router, Hono RPC APIs, Drizzle/Postgres, TanStack Query, Better Auth, Azure. Scaffold new repos, add modules, and enforce code conventions.
- **[poc-from-sow](./poc-from-sow/SKILL.md)**: Turn a SOW into a customer-validatable, continuation-ready POC codebase on the Forward Path stack — buildable, runnable, demo-deployable, with an agent-ready handoff pack — by orchestrating web-ui / mobile-ui / product-foundation / azure-conventions, then closing with a poc-to-product-architecture canvas + DOCX.
- **[standup-report](./standup-report/SKILL.md)**: Generate a narratable daily standup (yesterday / today / blockers) for yourself or a named user from Linear issues, GitHub merged/open PRs, and local Cursor chat transcripts.
- **[inbox-brief](./inbox-brief/SKILL.md)**: Context brief of today's Outlook inbox (or named emails) — scrapes Outlook Web via a persistent Playwright profile (no Graph API/admin consent), filters GitHub/automated noise, and enriches each human thread with related Linear issues and local Cursor chats.
- **[project-update-writer](./project-update-writer/SKILL.md)**: Summarize everything shipped in a Linear project since its last status update — baseline from the latest update, issues completed since grouped by capability area — and post a new project update with health after the user confirms.
- **[e2e-testing](./e2e-testing/SKILL.md)**: Implement tester-army's e2e library, build user-journey coverage, and run the suite in the merge queue without executing E2E tests on every PR.
- **[ci-cd](./ci-cd/SKILL.md)**: Set up or review GitHub Actions pipelines with PR builds, full merge-queue validation, required-check enforcement, canonical job/stage names, and Turbo remote caching. Included in the standard bootstrap; [naming and reporting contract](./ci-cd/references/naming.md), [caching reference](./ci-cd/references/caching.md).
- **[t3-thread-follow](./t3-thread-follow/SKILL.md)**: Find T3 Code threads by title, ID, or description, then use their context, build on their work, or wait for a result across providers.
- **[get-forwardpath-skills](./get-forwardpath-skills/SKILL.md)**: Install the standard Forward Path skill set into the current project for Claude Code, Cursor, and Codex: execution, PRs, code and security reviews, releases, Linear, Azure conventions and operations, Infisical, plus improve, unslop, grill-with-docs, and the Better Auth, Effect, and Drizzle skills.
