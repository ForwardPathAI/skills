# Forward Path Skills

Agent skills published by [Forward Path](https://forwardpath.ai) for use with Claude Code and other agents that follow the [skills.sh](https://www.skills.sh) format.

## Install

To set up a project with the standard Forward Path skill set (our execution, PR, review, release, Linear, Azure, and secrets skills plus vetted Effect, Drizzle, Better Auth, and writing skills), install the bootstrap skill and ask your agent to run it:

```bash
npx skills add forwardpathai/skills -s get-forwardpath-skills -a claude-code cursor codex -y
```

Install any skill in this repo with the [skills CLI](https://www.skills.sh/docs/cli):

```bash
npx skills add forwardpathai/skills
```

Or install a single skill by name:

```bash
npx skills add forwardpathai/skills --skill issue-writer
```

List every skill in the repo with `npx skills add forwardpathai/skills --list`.

Install `ci-cd` alongside workflow-authoring skills such as `product-foundation`, `azure-conventions`, `e2e-testing`, and `linear-release-setup`. The standard `get-forwardpath-skills` bootstrap includes it.

## Skills

Skills live in bucket folders under `skills/`. Each bucket's `README.md` lists its skills with a one-line description.

| Bucket | Holds |
|--------|-------|
| [engineering](./skills/engineering/README.md) | Skills we use: code, PRs, CI/CD, releases, Linear, Azure, client delivery, and reporting. |
| [in-progress](./skills/in-progress/README.md) | Beta skills. Public on purpose, can change without notice, kept out of the bootstrap. |
| [deprecated](./skills/deprecated/README.md) | Skills we no longer use, each with what replaced it. |

A skill moves between buckets with `git mv`; its name stays the same, so installs by name keep working.

## Authoring

Each skill lives in its own directory inside a bucket, with a `SKILL.md` entry point that has YAML frontmatter. A skill may also bundle reference docs and utility scripts alongside it:

```
skills/
└── <bucket>/
    ├── README.md             # lists every skill in the bucket
    └── <skill-name>/
        ├── SKILL.md          # required entry point
        ├── REFERENCE.md      # optional reference docs
        └── scripts/          # optional utility scripts
```

Reference files and scripts must be addressed relative to the skill's own directory (never hardcode an absolute install path), so the skill keeps working wherever `skills.sh` installs it.

Link another skill as `../<other-skill>/SKILL.md`. `skills.sh` installs skills side by side, so that path resolves after install, and in the repo it resolves within one bucket. Skills in `engineering/` link only to other `engineering/` skills.

The `name` in frontmatter must match the directory name. The `description` is what agents match against to decide whether to invoke the skill — make it specific about *when* the skill should fire.

When you add, move, or remove a skill, update its bucket's `README.md`.

## License

MIT
