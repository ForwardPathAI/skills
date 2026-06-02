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
npx skills add forwardpathai/skills/azure-infra-setup
npx skills add forwardpathai/skills/engineering-projects-on-track
```

## Skills

| Skill | Description |
|-------|-------------|
| [issue-writer](./issue-writer) | Write Linear issues that an AI coding agent can execute without follow-up questions. |
| [open-pr](./open-pr) | Open a GitHub PR from local changes via a Linear issue, Linear's git branch, commit, and `gh`. |
| [stack-pr](./stack-pr) | Open a stacked/dependent GitHub PR based on the current branch (sibling of open-pr) via a Linear issue, commit, and `gh`. |
| [cloud-agent-pr-stats](./cloud-agent-pr-stats) | Count PRs opened by cloud coding agents (Cursor, Codex, Devin, Claude, Copilot) across a GitHub org, by branch-name prefix. |
| [engineering-projects-on-track](./engineering-projects-on-track) | On-track % for ForwardPath Engineering Linear projects in In Progress or UAT, from the latest project status update. |
| [azure-infra-setup](./azure-infra-setup) | Author Forward Path Azure infrastructure (Terraform/Bicep) — shared ACR, OIDC/RBAC, environments, Key Vault, Container Apps. |

## Authoring

Each skill lives in its own directory at the repo root and contains a single `SKILL.md` with YAML frontmatter:

```
skills/
└── <skill-name>/
    └── SKILL.md
```

The `name` in frontmatter must match the directory name. The `description` is what agents match against to decide whether to invoke the skill — make it specific about *when* the skill should fire.

## License

MIT
