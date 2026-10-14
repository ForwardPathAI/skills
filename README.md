# Forward Path Skills

Agent skills published by [Forward Path](https://forwardpath.ai) for use with Claude Code and other agents that follow the [skills.sh](https://www.skills.sh) format.

## Install

Install any skill in this repo with the [skills CLI](https://www.skills.sh/docs/cli):

```bash
npx skills add forwardpathai/skills
```

Or install a single skill by name:

```bash
npx skills add forwardpathai/skills/setup-fp-skills
npx skills add forwardpathai/skills/issue-writer
npx skills add forwardpathai/skills/pr-open
npx skills add forwardpathai/skills/open-pr
npx skills add forwardpathai/skills/open-pr-with-screenshots
npx skills add forwardpathai/skills/release
npx skills add forwardpathai/skills/stack-pr
npx skills add forwardpathai/skills/maintain-pr
npx skills add forwardpathai/skills/cloud-agent-pr-stats
npx skills add forwardpathai/skills/backlog-hygiene
npx skills add forwardpathai/skills/ticket-refiner
npx skills add forwardpathai/skills/azure-infra-setup
npx skills add forwardpathai/skills/engineering-projects-on-track
npx skills add forwardpathai/skills/mobile-ui
npx skills add forwardpathai/skills/mobile-ui-implement
npx skills add forwardpathai/skills/web-ui
npx skills add forwardpathai/skills/customer-deployment-package
npx skills add forwardpathai/skills/review-mp4
npx skills add forwardpathai/skills/azure-hibernate
npx skills add forwardpathai/skills/qa-test-plan
npx skills add forwardpathai/skills/qa-test-plan-setup
npx skills add forwardpathai/skills/teach-web-actions
npx skills add forwardpathai/skills/product-foundation
npx skills add forwardpathai/skills/linear-release-setup
npx skills add forwardpathai/skills/linear-backlog-grill
npx skills add forwardpathai/skills/plan-refiner
npx skills add forwardpathai/skills/plan-context-imager
npx skills add forwardpathai/skills/speclang-writer
npx skills add forwardpathai/skills/prototype
npx skills add forwardpathai/skills/poc-to-product-architecture
npx skills add forwardpathai/skills/architecture-to-linear-plan
npx skills add forwardpathai/skills/standup-report
npx skills add forwardpathai/skills/inbox-brief
npx skills add forwardpathai/skills/project-update-writer
npx skills add forwardpathai/skills/effort-estimate
npx skills add forwardpathai/skills/eng-report-effort-estimate
npx skills add forwardpathai/skills/setup-preview-env
npx skills add forwardpathai/skills/t3-thread-follow
npx skills add forwardpathai/skills/security-sweep
```

## Skills

| Skill | Description |
|-------|-------------|
| [setup-fp-skills](./setup-fp-skills) | Route Forward Path work to the relevant workflow and load its dependencies only when needed. |
| [issue-writer](./issue-writer) | Draft, create, or update executable Linear issues, with explicit modes and one owner for issue writes. |
| [pr-open](./pr-open) | Shared PR workflow for standard, stacked, and prepared branches; explicit tracking policy and existing-PR reuse. |
| [open-pr](./open-pr) | Compatibility entry point for pr-open with Linear tracking. |
| [release](./release) | Cut a production GitHub release from the default branch — semver tag, release notes, breaking-change gate, and CI watch. |
| [stack-pr](./stack-pr) | Compatibility entry point for pr-open in stacked mode with Linear tracking. |
| [open-pr-with-screenshots](./open-pr-with-screenshots) | Extend normal, stacked, or existing PR work with verified screenshots of the actual UI changes, embedded in the PR description. Install with `open-pr`, or `stack-pr` for stacks. |
| [maintain-pr](./maintain-pr) | Maintain an open GitHub PR through Greptile and human review feedback, merge conflicts, and CI failures — triage every finding, fix, validate, push, reply/resolve, and recheck the latest head until it is ready or concretely blocked. |
| [cloud-agent-pr-stats](./cloud-agent-pr-stats) | Count PRs opened by cloud coding agents (Cursor, Codex, Devin, Claude, Copilot) across a GitHub org, by branch-name prefix. |
| [backlog-hygiene](./backlog-hygiene) | Scan a Linear project's backlog for relevance — flag stale, already-shipped, or duplicated issues using update age, code/PR evidence, and ticket similarity — then apply confirmed actions one at a time. |
| [ticket-refiner](./ticket-refiner) | Resolve missing intent through a focused interview, then return a draft or save an approved rewrite through issue-writer. |
| [engineering-projects-on-track](./engineering-projects-on-track) | On-track % for ForwardPath Engineering Linear projects in In Progress or UAT, from the latest project status update. |
| [azure-infra-setup](./azure-infra-setup) | Author Forward Path Azure infrastructure (Terraform/Bicep) — shared ACR, OIDC/RBAC, environments, Key Vault, Container Apps. |
| [mobile-ui](./mobile-ui) | Turn a SOW into a grounded Expo SDK 54 screen spec and premium portrait UI mockups (via Google Gemini or OpenRouter, with a consent-gated on-device Apple-Silicon fallback when no cloud key is available). |
| [mobile-ui-implement](./mobile-ui-implement) | Turn mobile UI mockups (PNG screens or a PDF deck) into per-screen implementation blueprints, then build them in an Expo Go-compatible app — decomposing each screen into layers, components, states, and animations a weaker model can build one at a time. |
| [web-ui](./web-ui) | Turn a SOW and/or a real Next.js + Tailwind codebase into a grounded web screen spec and consistent desktop mockups (via Google Gemini or OpenRouter, with a consent-gated on-device Apple-Silicon fallback when no cloud key is available) — anchored by a brand style board and a persistent app-shell (nav/sidebar) so every screen looks like one credible product. |
| [customer-deployment-package](./customer-deployment-package) | Build a customer-facing deployment handoff — external Terraform/Bicep, setup instructions filled into the Notion template and saved to the deployments DB, then exported and zipped with a Windows-safe name. |
| [review-mp4](./review-mp4) | Understand an mp4 (local or URL): extract frames with ffmpeg, pick the sharpest in-focus frame per window via variance-of-Laplacian blur detection (Python or Node), then read them to answer questions. |
| [azure-hibernate](./azure-hibernate) | Hibernate a live client project's Azure resource group to minimum cost (scale/stop App Service Plans, web apps, SQL, Redis, databases via the `az` CLI) and wake it for retesting — reversibly, recording state before every change. |
| [qa-test-plan](./qa-test-plan) | Add QA test cases to the Notion QA Test Plan database — generate candidates from a feature change or the whole app, get QA approval, then append rows QA works through during full regression runs. |
| [qa-test-plan-setup](./qa-test-plan-setup) | Per-project one-time creation of a `<Project> — QA Test Plan` Notion database with the fixed Forward Path schema (test case, feature, steps, expected result, category, priority, status). |
| [teach-web-actions](./teach-web-actions) | Learn a website by recording a user-driven Chrome session (HAR + UI steps) via Playwright codegen, distill it into a reusable lesson (endpoints, payloads, parameter knobs, auth), then replay a variation with new parameters as an API call or as UI navigation captured to mp4. |
| [product-foundation](./product-foundation) | The standard stack and conventions for building Forward Path products — Bun monorepo, Next.js App Router, Hono RPC APIs, Drizzle/Postgres, TanStack Query, Better Auth, Azure. Scaffold new repos, add modules, and enforce code conventions. |
| [linear-release-setup](./linear-release-setup) | Set up GitHub Release workflows that publish containers, keep a scheduled Linear release in progress from main merges, and complete it when the customer GitHub Release ships. |
| [linear-backlog-grill](./linear-backlog-grill) | Grill Linear project backlogs for execution readiness — grade tickets, interview for missing specification, split oversized work, and rewrite issues to pass the agent-ready bar. |
| [plan-refiner](./plan-refiner) | Harden an existing Cursor plan so a weaker executor model can implement it without judgment calls — hunt unknowns, resolve them via codebase/web research or a one-gap-at-a-time user interview, anticipate non-obvious scenarios, and rewrite the plan file in place as unambiguous, verifiable statements. |
| [plan-context-imager](./plan-context-imager) | Gather the codebase context a plan depends on, render it into dense PNG pages via pxpipe's `renderTextToImages`, and embed the images plus a per-page index into the plan so the executor reads them instead of re-grepping the codebase each step. |
| [speclang-writer](./speclang-writer) | Turn a plan into a SpecLang specification — a structured, natural-language Markdown document (the single source of truth) that captures a system's behavior and its pinned implementation details so an AI toolchain or executor can generate the code from the spec. |
| [prototype](./prototype) | Turn a SOW into a customer-validatable, continuation-ready POC codebase on the Forward Path stack — buildable, runnable, demo-deployable, with an agent-ready handoff pack — by orchestrating web-ui / mobile-ui / product-foundation / azure-infra-setup, then closing with a poc-to-product-architecture canvas + DOCX. |
| [poc-to-product-architecture](./poc-to-product-architecture) | Turn a SOW and POC repo into a production system-design canvas — architecture, gap audit, Azure resource map, Bicep skeleton, security/reliability, and cost estimate, constrained to the Forward Path stack and customer-deployable Bicep. |
| [architecture-to-linear-plan](./architecture-to-linear-plan) | Turn the poc-to-product-architecture deliverable (canvas + DOCX) and any web-ui/mobile-ui mockups into a delivery plan — Linear milestones with proposed timelines and executable functional + design tickets — then, once approved, create the project, milestones, and issues in Linear via the Linear MCP. |
| [standup-report](./standup-report) | Generate a narratable daily standup (yesterday / today / blockers) for yourself or a named user from Linear issues, GitHub merged/open PRs, and local Cursor chat transcripts. |
| [inbox-brief](./inbox-brief) | Context brief of today's Outlook inbox (or named emails) — scrapes Outlook Web via a persistent Playwright profile (no Graph API/admin consent), filters GitHub/automated noise, and enriches each human thread with related Linear issues and local Cursor chats. |
| [project-update-writer](./project-update-writer) | Summarize everything shipped in a Linear project since its last status update — baseline from the latest update, issues completed since grouped by capability area — and post a new project update with health after the user confirms. |
| [effort-estimate](./effort-estimate) | Produce a bottom-up engineering-hours estimate for a feature, workstream, or software build, with explicit scope assumptions and quantified price levers. |
| [eng-report-effort-estimate](./eng-report-effort-estimate) | Generate the combined Engineering Report + Effort Estimate document in Notion for a custom build — understanding check with price levers, gated generation, fixed-price effort estimation with internal QA phase, and a post-generation coverage audit. |
| [security-sweep](./security-sweep) | Sweep a GitHub org for open Dependabot alerts and open one grouped fix PR per repo per ecosystem — deduped by package, skipping alerts an existing PR already covers, verified before push. |
| [setup-preview-env](./setup-preview-env) | Set up ephemeral per-pull-request Azure preview environments for a containerized app — shared/per-PR Terraform, GitHub Actions deploy/teardown, auth redirects, and runbooks distilled from the ButtconRAG preview lane. |
| [t3-thread-follow](./t3-thread-follow) | Find T3 Code threads by title, ID, or description, then use their context, build on their work, or wait for a result across providers. |

## Shared workflows

Use `pr-open` for new callers. `open-pr` and `stack-pr` remain small compatibility entry points, including the repo-local `.agents/skills/open-pr` entry point.

| Workflow | Calls | Responsibility kept by the workflow |
|---|---|---|
| Ordinary or stacked PR | `pr-open` → `issue-writer` in create mode when tracking is missing | Scope of the requested change |
| Security sweep | `pr-open` in prepared mode with no Linear tracking | Alert grouping, dependency fixes, verification, advisory content |
| SDK release | `pr-open` in prepared mode with no Linear tracking | Version bump, checks, merge, release approval, publishing |
| Backlog refinement | `ticket-refiner` in draft mode → `issue-writer` in draft mode; after review, create/update modes | Backlog selection, approval, and refinement comment |
| Delivery planning | `issue-writer` in draft mode, then create/update modes after approval | Milestones, scheduling, project and grouping document |
| Engineering scoping | `effort-estimate` | Report structure, scoping review, and Notion output |

Install required sibling skills alongside a workflow, or install the full repository. Skills must resolve missing siblings through the session catalog or installed skill roots rather than assuming a full-repository install. `setup-fp-skills` installs or reads only selected dependencies, not the whole roster.

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

### Naming checks

New skills use `domain-action[-qualifier]`, such as `pr-open`, `issue-refine`, or `ui-design-mobile`. Use lowercase kebab-case, at most 63 characters. The full rule is in [AGENTS.md](AGENTS.md), with the allowed vocabulary and exceptions in [skill-naming.json](skill-naming.json).

`prototype` and `setup-fp-skills` are approved names. Existing nonconforming names have explicit migration exceptions; do not add new skills to that legacy list. The check also validates repo-local wrappers under `.agents`, `.claude`, `.codex`, and `.cursor`.

```bash
python3 scripts/lint_skill_names.py
python3 -m unittest discover -s tests -p 'test_skill_names.py'
```

The [Skill naming workflow](.github/workflows/skill-names.yml) runs both commands on pushes and pull requests. Spelling and structure are checked automatically; whether a name accurately describes its responsibility remains a review decision.

### Composing skills

Give each reusable procedure one owner. Callers name the skill, requested mode, inputs, returned result, and which workflow owns external writes. Pass existing artifact IDs, current evidence, and approval already obtained; do not repeat a completed write or interview.

Use draft mode when a caller needs a reviewable proposal before saving. Draft mode applies to all side effects, including comments, grouping documents, and split issues. Keep workflow-specific policies with the caller, such as security branch prefixes or release approval gates.

Read dependencies when their step begins. Keep detailed mode-specific instructions in linked reference files. Compatibility entry points forward inputs to the canonical skill and contain no copy of its procedure.

## License

MIT
