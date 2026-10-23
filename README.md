# Forward Path Skills

Agent skills published by [Forward Path](https://forwardpath.ai) for use with Claude Code and other agents that follow the [skills.sh](https://www.skills.sh) format.

## Install

To set up a project with the standard Forward Path skill set (our PR, release, and Linear skills plus vetted Effect, Drizzle, Better Auth, and writing skills), install the bootstrap skill and ask your agent to run it:

```bash
npx skills add forwardpathai/skills -s get-forwardpath-skills -a claude-code cursor codex -y
```

Install any skill in this repo with the [skills CLI](https://www.skills.sh/docs/cli):

```bash
npx skills add forwardpathai/skills
```

Or install a single skill by name:

```bash
npx skills add forwardpathai/skills/issue-writer
npx skills add forwardpathai/skills/open-pr
npx skills add forwardpathai/skills/open-pr-with-screenshots
npx skills add forwardpathai/skills/release
npx skills add forwardpathai/skills/maintain-pr
npx skills add forwardpathai/skills/auto-pilot-pr
npx skills add forwardpathai/skills/execute
npx skills add forwardpathai/skills/code-review
npx skills add forwardpathai/skills/security-review
npx skills add forwardpathai/skills/cloud-agent-pr-stats
npx skills add forwardpathai/skills/cloud-agent-triage
npx skills add forwardpathai/skills/backlog-hygiene
npx skills add forwardpathai/skills/ticket-refiner
npx skills add forwardpathai/skills/azure-conventions
npx skills add forwardpathai/skills/azure-ops
npx skills add forwardpathai/skills/infisical
npx skills add forwardpathai/skills/engineering-projects-on-track
npx skills add forwardpathai/skills/mobile-ui
npx skills add forwardpathai/skills/mobile-ui-implement
npx skills add forwardpathai/skills/web-ui
npx skills add forwardpathai/skills/customer-deployment-package
npx skills add forwardpathai/skills/review-mp4
npx skills add forwardpathai/skills/qa-test-plan
npx skills add forwardpathai/skills/qa-test-plan-setup
npx skills add forwardpathai/skills/teach-web-actions
npx skills add forwardpathai/skills/product-foundation
npx skills add forwardpathai/skills/linear-release-setup
npx skills add forwardpathai/skills/linear-backlog-grill
npx skills add forwardpathai/skills/plan-refiner
npx skills add forwardpathai/skills/plan-context-imager
npx skills add forwardpathai/skills/speclang-writer
npx skills add forwardpathai/skills/poc-from-sow
npx skills add forwardpathai/skills/poc-to-product-architecture
npx skills add forwardpathai/skills/architecture-to-linear-plan
npx skills add forwardpathai/skills/standup-report
npx skills add forwardpathai/skills/inbox-brief
npx skills add forwardpathai/skills/project-update-writer
npx skills add forwardpathai/skills/effort-estimate
npx skills add forwardpathai/skills/eng-report-effort-estimate
npx skills add forwardpathai/skills/setup-preview-env
npx skills add forwardpathai/skills/t3-thread-follow
npx skills add forwardpathai/skills/get-forwardpath-skills
```

## Skills

| Skill | Description |
|-------|-------------|
| [issue-writer](./issue-writer) | Write Linear issues an AI coding agent can execute without follow-up questions. |
| [open-pr](./open-pr) | Open GitHub PRs from local changes via a Linear issue, Linear's git branch, commit, and `gh` — and decide whether to ship one PR, split it, or stack dependent PRs. |
| [open-pr-with-screenshots](./open-pr-with-screenshots) | Extend normal, stacked, or existing PR work with verified screenshots of the actual UI changes, embedded in the PR description. Install with `open-pr`. |
| [release](./release) | Cut a production GitHub release from the default branch — semver tag, release notes, breaking-change gate, and CI watch. |
| [maintain-pr](./maintain-pr) | Maintain an open GitHub PR through Greptile and human review feedback, merge conflicts, and CI failures — triage every finding, fix, validate, push, reply/resolve, and recheck the latest head until it is ready or concretely blocked. |
| [auto-pilot-pr](./auto-pilot-pr) | Run maintain-pr until the latest head is ready, then arm GitHub auto-merge on it. Disarms before each of its own pushes, so its unverified heads never merge. Install with `maintain-pr`. |
| [execute](./execute) | Run one written spec (improve plan, Linear issue, or GitHub issue) through to a PR that has merged or is armed to merge: an executor subagent builds it in a worktree, the lead agent reviews the diff, then runs code-review, simplify, open-pr, and auto-pilot-pr. Install with `open-pr`, `issue-writer`, `maintain-pr`, and `auto-pilot-pr`. |
| [code-review](./code-review) | Review a working-tree diff, branch, or specified PR for evidence-backed correctness bugs and regressions. |
| [security-review](./security-review) | Review a working-tree diff, branch, or specified PR for vulnerabilities with verified attack paths and severity. |
| [cloud-agent-pr-stats](./cloud-agent-pr-stats) | Count PRs opened by cloud coding agents (Cursor, Codex, Devin, Claude, Copilot) across a GitHub org, by branch-name prefix. |
| [cloud-agent-triage](./cloud-agent-triage) | Evaluate whether Linear tickets suit autonomous Cursor cloud agents (why yes / why not), triage a repo's backlog honoring blockers, and optionally delegate the ready ones to Cursor. |
| [backlog-hygiene](./backlog-hygiene) | Scan a Linear project's backlog for relevance — flag stale, already-shipped, or duplicated issues using update age, code/PR evidence, and ticket similarity — then apply confirmed actions one at a time. |
| [ticket-refiner](./ticket-refiner) | Interview the person who knows why a Linear ticket exists and rewrite it to pass issue-writer's agent-ready bar; the gap-driven interview step neither backlog-hygiene nor cloud-agent-triage has. |
| [engineering-projects-on-track](./engineering-projects-on-track) | On-track % for ForwardPath Engineering Linear projects in In Progress or UAT, from the latest project status update. |
| [azure-conventions](./azure-conventions) | Forward Path Azure conventions — resource naming, environments, regions, Container Apps, shared ACR, OIDC/RBAC, Key Vault, and known gotchas. |
| [azure-ops](./azure-ops) | Inspect and operate live Azure apps with the `az` CLI — locate resources, stream and query logs, check revisions, images, identities, and secrets, and follow symptom playbooks for failed deploys, 5xx errors, and database or Key Vault failures. |
| [infisical](./infisical) | Forward Path's app and CI/CD secrets rules — Infisical as the single source of truth, no local `.env` files, and Secret Syncs into GitHub and Azure Key Vault. |
| [mobile-ui](./mobile-ui) | Turn a SOW into a grounded Expo SDK 54 screen spec and premium portrait UI mockups (via Google Gemini or OpenRouter, with a consent-gated on-device Apple-Silicon fallback when no cloud key is available). |
| [mobile-ui-implement](./mobile-ui-implement) | Turn mobile UI mockups (PNG screens or a PDF deck) into per-screen implementation blueprints, then build them in an Expo Go-compatible app — decomposing each screen into layers, components, states, and animations a weaker model can build one at a time. |
| [web-ui](./web-ui) | Turn a SOW and/or a real Next.js + Tailwind codebase into a grounded web screen spec and consistent desktop mockups (via Google Gemini or OpenRouter, with a consent-gated on-device Apple-Silicon fallback when no cloud key is available) — anchored by a brand style board and a persistent app-shell (nav/sidebar) so every screen looks like one credible product. |
| [customer-deployment-package](./customer-deployment-package) | Build a customer-facing deployment handoff — external Terraform/Bicep, setup instructions filled into the Notion template and saved to the deployments DB, then exported and zipped with a Windows-safe name. |
| [review-mp4](./review-mp4) | Understand an mp4 (local or URL): extract frames with ffmpeg, pick the sharpest in-focus frame per window via variance-of-Laplacian blur detection (Python or Node), then read them to answer questions. |
| [qa-test-plan](./qa-test-plan) | Add QA test cases to the Notion QA Test Plan database — generate candidates from a feature change or the whole app, get QA approval, then append rows QA works through during full regression runs. |
| [qa-test-plan-setup](./qa-test-plan-setup) | Per-project one-time creation of a `<Project> — QA Test Plan` Notion database with the fixed Forward Path schema (test case, feature, steps, expected result, category, priority, status). |
| [teach-web-actions](./teach-web-actions) | Learn a website by recording a user-driven Chrome session (HAR + UI steps) via Playwright codegen, distill it into a reusable lesson (endpoints, payloads, parameter knobs, auth), then replay a variation with new parameters as an API call or as UI navigation captured to mp4. |
| [product-foundation](./product-foundation) | The standard stack and conventions for building Forward Path products — Bun monorepo, Next.js App Router, Hono RPC APIs, Drizzle/Postgres, TanStack Query, Better Auth, Azure. Scaffold new repos, add modules, and enforce code conventions. |
| [linear-release-setup](./linear-release-setup) | Set up GitHub Release workflows that publish containers, keep a scheduled Linear release in progress from main merges, and complete it when the customer GitHub Release ships. |
| [linear-backlog-grill](./linear-backlog-grill) | Grill Linear project backlogs for execution readiness — grade tickets, interview for missing specification, split oversized work, and rewrite issues to pass the agent-ready bar. |
| [plan-refiner](./plan-refiner) | Harden an existing Cursor plan so a weaker executor model can implement it without judgment calls — hunt unknowns, resolve them via codebase/web research or a one-gap-at-a-time user interview, anticipate non-obvious scenarios, and rewrite the plan file in place as unambiguous, verifiable statements. |
| [plan-context-imager](./plan-context-imager) | Gather the codebase context a plan depends on, render it into dense PNG pages via pxpipe's `renderTextToImages`, and embed the images plus a per-page index into the plan so the executor reads them instead of re-grepping the codebase each step. |
| [speclang-writer](./speclang-writer) | Turn a plan into a SpecLang specification — a structured, natural-language Markdown document (the single source of truth) that captures a system's behavior and its pinned implementation details so an AI toolchain or executor can generate the code from the spec. |
| [poc-from-sow](./poc-from-sow) | Turn a SOW into a customer-validatable, continuation-ready POC codebase on the Forward Path stack — buildable, runnable, demo-deployable, with an agent-ready handoff pack — by orchestrating web-ui / mobile-ui / product-foundation / azure-conventions, then closing with a poc-to-product-architecture canvas + DOCX. |
| [poc-to-product-architecture](./poc-to-product-architecture) | Turn a SOW and POC repo into a production system-design canvas — architecture, gap audit, Azure resource map, Bicep skeleton, security/reliability, and cost estimate, constrained to the Forward Path stack and customer-deployable Bicep. |
| [architecture-to-linear-plan](./architecture-to-linear-plan) | Turn the poc-to-product-architecture deliverable (canvas + DOCX) and any web-ui/mobile-ui mockups into a delivery plan — Linear milestones with proposed timelines and executable functional + design tickets — then, once approved, create the project, milestones, and issues in Linear via the Linear MCP. |
| [standup-report](./standup-report) | Generate a narratable daily standup (yesterday / today / blockers) for yourself or a named user from Linear issues, GitHub merged/open PRs, and local Cursor chat transcripts. |
| [inbox-brief](./inbox-brief) | Context brief of today's Outlook inbox (or named emails) — scrapes Outlook Web via a persistent Playwright profile (no Graph API/admin consent), filters GitHub/automated noise, and enriches each human thread with related Linear issues and local Cursor chats. |
| [project-update-writer](./project-update-writer) | Summarize everything shipped in a Linear project since its last status update — baseline from the latest update, issues completed since grouped by capability area — and post a new project update with health after the user confirms. |
| [effort-estimate](./effort-estimate) | Produce a bottom-up engineering-hours estimate for a feature, workstream, or software build, with explicit scope assumptions and quantified price levers. |
| [eng-report-effort-estimate](./eng-report-effort-estimate) | Generate the combined Engineering Report + Effort Estimate document in Notion for a custom build — understanding check with price levers, gated generation, fixed-price effort estimation with internal QA phase, and a post-generation coverage audit. |
| [setup-preview-env](./setup-preview-env) | Set up ephemeral per-pull-request Azure preview environments for a containerized app — shared/per-PR Terraform, GitHub Actions deploy/teardown, auth redirects, and runbooks distilled from the ButtconRAG preview lane. |
| [t3-thread-follow](./t3-thread-follow) | Find T3 Code threads by title, ID, or description, then use their context, build on their work, or wait for a result across providers. |
| [get-forwardpath-skills](./get-forwardpath-skills) | Install the standard Forward Path skill set into the current project for Claude Code, Cursor, and Codex — open-pr, maintain-pr, release, issue-writer, plus improve, unslop, grill-with-docs, and the Better Auth, Effect, and Drizzle skills. |

## Authoring

Each skill lives in its own directory at the repo root with a `SKILL.md` entry point that has YAML frontmatter. A skill may also bundle reference docs and utility scripts alongside it:

```
skills/
└── <skill-name>/
    ├── SKILL.md          # required entry point
    ├── REFERENCE.md      # optional reference docs
    └── scripts/          # optional utility scripts
```

Reference files and scripts must be addressed relative to the skill's own directory (never hardcode an absolute install path), so the skill keeps working wherever `skills.sh` installs it.

The `name` in frontmatter must match the directory name. The `description` is what agents match against to decide whether to invoke the skill — make it specific about *when* the skill should fire.

## License

MIT
