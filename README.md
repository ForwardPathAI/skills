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
npx skills add forwardpathai/skills/stack-pr
npx skills add forwardpathai/skills/cloud-agent-pr-stats
npx skills add forwardpathai/skills/cloud-agent-triage
npx skills add forwardpathai/skills/azure-infra-setup
npx skills add forwardpathai/skills/engineering-projects-on-track
npx skills add forwardpathai/skills/mobile-ui
npx skills add forwardpathai/skills/customer-deployment-package
npx skills add forwardpathai/skills/review-mp4
```

## Skills

| Skill | Description |
|-------|-------------|
| [issue-writer](./issue-writer) | Write Linear issues an AI coding agent can execute without follow-up questions. |
| [open-pr](./open-pr) | Open a GitHub PR from local changes via a Linear issue, Linear's git branch, commit, and `gh`. |
| [stack-pr](./stack-pr) | Open a stacked/dependent GitHub PR based on the current branch (sibling of open-pr) via a Linear issue, commit, and `gh`. |
| [cloud-agent-pr-stats](./cloud-agent-pr-stats) | Count PRs opened by cloud coding agents (Cursor, Codex, Devin, Claude, Copilot) across a GitHub org, by branch-name prefix. |
| [cloud-agent-triage](./cloud-agent-triage) | Evaluate whether Linear tickets suit autonomous Cursor cloud agents (why yes / why not), triage a repo's backlog honoring blockers, and optionally delegate the ready ones to Cursor. |
| [engineering-projects-on-track](./engineering-projects-on-track) | On-track % for ForwardPath Engineering Linear projects in In Progress or UAT, from the latest project status update. |
| [azure-infra-setup](./azure-infra-setup) | Author Forward Path Azure infrastructure (Terraform/Bicep) — shared ACR, OIDC/RBAC, environments, Key Vault, Container Apps. |
| [mobile-ui](./mobile-ui) | Turn a SOW into a grounded Expo SDK 54 screen spec and premium portrait UI mockups (via Google Gemini). |
| [customer-deployment-package](./customer-deployment-package) | Build a customer-facing deployment handoff — external Terraform/Bicep, setup instructions filled into the Notion template and saved to the deployments DB, then exported and zipped with a Windows-safe name. |
| [review-mp4](./review-mp4) | Understand an mp4 (local or URL): extract frames with ffmpeg, pick the sharpest in-focus frame per window via variance-of-Laplacian blur detection (Python or Node), then read them to answer questions. |

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
