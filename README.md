# Forward Path Skills

Agent skills published by [Forward Path](https://forwardpath.ai) for use with Claude Code and other agents that follow the [skills.sh](https://www.skills.sh) format.

## Install

Install any skill in this repo with the [skills CLI](https://www.skills.sh/docs/cli):

```bash
npx skills add forwardpathai/skills
```

Or install a single skill by name:

```bash
npx skills add forwardpathai/skills/issue-writer
npx skills add forwardpathai/skills/open-pr
npx skills add forwardpathai/skills/release
npx skills add forwardpathai/skills/stack-pr
npx skills add forwardpathai/skills/cloud-agent-pr-stats
npx skills add forwardpathai/skills/cloud-agent-triage
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
npx skills add forwardpathai/skills/teach-web-actions
npx skills add forwardpathai/skills/product-foundation
npx skills add forwardpathai/skills/linear-backlog-grill
npx skills add forwardpathai/skills/plan-refiner
npx skills add forwardpathai/skills/plan-context-imager
npx skills add forwardpathai/skills/speclang-writer
npx skills add forwardpathai/skills/poc-to-product-architecture
npx skills add forwardpathai/skills/standup-report
```

## Skills

| Skill | Description |
|-------|-------------|
| [issue-writer](./issue-writer) | Write Linear issues an AI coding agent can execute without follow-up questions. |
| [open-pr](./open-pr) | Open a GitHub PR from local changes via a Linear issue, Linear's git branch, commit, and `gh`. |
| [release](./release) | Cut a production GitHub release from the default branch — semver tag, release notes, breaking-change gate, and CI watch. |
| [stack-pr](./stack-pr) | Open a stacked/dependent GitHub PR based on the current branch (sibling of open-pr) via a Linear issue, commit, and `gh`. |
| [cloud-agent-pr-stats](./cloud-agent-pr-stats) | Count PRs opened by cloud coding agents (Cursor, Codex, Devin, Claude, Copilot) across a GitHub org, by branch-name prefix. |
| [cloud-agent-triage](./cloud-agent-triage) | Evaluate whether Linear tickets suit autonomous Cursor cloud agents (why yes / why not), triage a repo's backlog honoring blockers, and optionally delegate the ready ones to Cursor. |
| [backlog-hygiene](./backlog-hygiene) | Scan a Linear project's backlog for relevance — flag stale, already-shipped, or duplicated issues using update age, code/PR evidence, and ticket similarity — then apply confirmed actions one at a time. |
| [ticket-refiner](./ticket-refiner) | Interview the person who knows why a Linear ticket exists and rewrite it to pass issue-writer's agent-ready bar; the gap-driven interview step neither backlog-hygiene nor cloud-agent-triage has. |
| [engineering-projects-on-track](./engineering-projects-on-track) | On-track % for ForwardPath Engineering Linear projects in In Progress or UAT, from the latest project status update. |
| [azure-infra-setup](./azure-infra-setup) | Author Forward Path Azure infrastructure (Terraform/Bicep) — shared ACR, OIDC/RBAC, environments, Key Vault, Container Apps. |
| [mobile-ui](./mobile-ui) | Turn a SOW into a grounded Expo SDK 54 screen spec and premium portrait UI mockups (via Google Gemini). |
| [mobile-ui-implement](./mobile-ui-implement) | Turn mobile UI mockups (PNG screens or a PDF deck) into per-screen implementation blueprints, then build them in an Expo Go-compatible app — decomposing each screen into layers, components, states, and animations a weaker model can build one at a time. |
| [web-ui](./web-ui) | Turn a SOW and/or a real Next.js + Tailwind codebase into a grounded web screen spec and consistent desktop mockups (via Google Gemini) — anchored by a brand style board and a persistent app-shell (nav/sidebar) so every screen looks like one credible product. |
| [customer-deployment-package](./customer-deployment-package) | Build a customer-facing deployment handoff — external Terraform/Bicep, setup instructions filled into the Notion template and saved to the deployments DB, then exported and zipped with a Windows-safe name. |
| [review-mp4](./review-mp4) | Understand an mp4 (local or URL): extract frames with ffmpeg, pick the sharpest in-focus frame per window via variance-of-Laplacian blur detection (Python or Node), then read them to answer questions. |
| [azure-hibernate](./azure-hibernate) | Hibernate a live client project's Azure resource group to minimum cost (scale/stop App Service Plans, web apps, SQL, Redis, databases via the `az` CLI) and wake it for retesting — reversibly, recording state before every change. |
| [qa-test-plan](./qa-test-plan) | Generate and maintain customer-shareable QA test plans for a Forward Path app from its code surface (routes/endpoints/flags); audit for coverage drift, sync after feature changes, and publish to Notion for collaborative QA. |
| [teach-web-actions](./teach-web-actions) | Learn a website by recording a user-driven Chrome session (HAR + UI steps) via Playwright codegen, distill it into a reusable lesson (endpoints, payloads, parameter knobs, auth), then replay a variation with new parameters as an API call or as UI navigation captured to mp4. |
| [product-foundation](./product-foundation) | The standard stack and conventions for building Forward Path products — Bun monorepo, Next.js App Router, Hono RPC APIs, Drizzle/Postgres, TanStack Query, Better Auth, Azure. Scaffold new repos, add modules, and enforce code conventions. |
| [linear-backlog-grill](./linear-backlog-grill) | Grill Linear project backlogs for execution readiness — grade tickets, interview for missing specification, split oversized work, and rewrite issues to pass the agent-ready bar. |
| [plan-refiner](./plan-refiner) | Harden an existing Cursor plan so a weaker executor model can implement it without judgment calls — hunt unknowns, resolve them via codebase/web research or a one-gap-at-a-time user interview, anticipate non-obvious scenarios, and rewrite the plan file in place as unambiguous, verifiable statements. |
| [plan-context-imager](./plan-context-imager) | Gather the codebase context a plan depends on, render it into dense PNG pages via pxpipe's `renderTextToImages`, and embed the images plus a per-page index into the plan so the executor reads them instead of re-grepping the codebase each step. |
| [speclang-writer](./speclang-writer) | Turn a plan into a SpecLang specification — a structured, natural-language Markdown document (the single source of truth) that captures a system's behavior and its pinned implementation details so an AI toolchain or executor can generate the code from the spec. |
| [poc-to-product-architecture](./poc-to-product-architecture) | Turn a SOW and POC repo into a production system-design canvas — architecture, gap audit, Azure resource map, Bicep skeleton, security/reliability, and cost estimate, constrained to the Forward Path stack and customer-deployable Bicep. |
| [standup-report](./standup-report) | Generate a narratable daily standup (yesterday / today / blockers) for yourself or a named user from Linear issues, GitHub merged/open PRs, and local Cursor chat transcripts. |

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
