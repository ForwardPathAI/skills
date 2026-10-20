---
name: get-forwardpath-skills
description: Install the standard Forward Path skill set into the current project for Claude Code, Cursor, and Codex — Forward Path PR, release, and Linear skills plus vetted outside skills for Effect, Drizzle/Postgres, Better Auth, codebase audits, and writing. Use when the user asks to set up, install, bootstrap, restore, or update Forward Path skills in a repo, or says "get forward path skills".
---

# Get Forward Path Skills

Install the standard skill set into the current repo, at project scope, for Claude Code, Cursor, and Codex. One run, no prompts.

## The set

| Skill | Source | Use |
|-------|--------|-----|
| get-forwardpath-skills | `forwardpathai/skills` | This skill, so teammates can rerun or update the set |
| open-pr | `forwardpathai/skills` | Open a PR via a Linear issue and Linear's branch |
| maintain-pr | `forwardpathai/skills` | Drive an open PR through review, conflicts, and CI |
| release | `forwardpathai/skills` | Cut a production GitHub release |
| issue-writer | `forwardpathai/skills` | Write agent-ready Linear issues |
| improve | `shadcn/improve` | Read-only codebase audit that writes handoff plans |
| unslop | `cursor/plugins` | Cut AI tells from writing |
| grill-with-docs | `mattpocock/skills` | Interview to sharpen a plan; writes ADRs and a glossary as it goes (manual call only) |
| better-auth-best-practices | `better-auth/skills` (official) | Better Auth server/client setup, adapters, sessions, plugins |
| create-auth | `better-auth/skills` (official) | Scaffold Better Auth into an app |
| better-auth-security-best-practices | `better-auth/skills` (official) | Rate limits, secrets, CSRF, cookie hardening |
| organization-best-practices | `better-auth/skills` (official) | Orgs, roles, RBAC via the organization plugin |
| effect-ts | `Effect-TS/skills` (official) | Set up a repo for Effect |
| postgres-drizzle | `ccheney/robust-skills` (community; Drizzle has no official skill) | Postgres schemas, queries, and Drizzle migrations |

## Prerequisites

- Run from the target project's git repo, not from `forwardpathai/skills` unless that is the project.
- `node` and `npx` on `PATH`.

Stop and tell the user what is missing if a prerequisite fails.

## Workflow

```
- [ ] Step 1: Go to the repo root
- [ ] Step 2: Install the set
- [ ] Step 3: Verify
- [ ] Step 4: Report
```

### Step 1: Go to the repo root

```bash
cd "$(git rev-parse --show-toplevel)"
```

If this fails, the user is not in a git repo. Ask which project to install into.

### Step 2: Install the set

Run each command on its own. If one fails, keep going and report it in Step 4. Never add `-g`: this set installs at project scope.

```bash
npx -y skills add forwardpathai/skills -s get-forwardpath-skills open-pr maintain-pr release issue-writer -a claude-code cursor codex -y
npx -y skills add shadcn/improve -s improve -a claude-code cursor codex -y
npx -y skills add cursor/plugins -s unslop -a claude-code cursor codex -y
npx -y skills add mattpocock/skills -s grill-with-docs -a claude-code cursor codex -y
npx -y skills add better-auth/skills -s better-auth-best-practices create-auth better-auth-security-best-practices organization-best-practices -a claude-code cursor codex -y
npx -y skills add Effect-TS/skills -s effect-ts -a claude-code cursor codex -y
npx -y skills add ccheney/robust-skills -s postgres-drizzle -a claude-code cursor codex -y
```

The CLI writes each skill to `.agents/skills/<name>/` (read by Cursor and Codex), links it from `.claude/skills/<name>`, and records it in `skills-lock.json`.

### Step 3: Verify

```bash
npx -y skills list
```

Check that all 14 skills from [The set](#the-set) appear. Rerun the command for any missing skill once; if it still fails, note the error.

### Step 4: Report

Tell the user:

1. Which skills installed and which failed, with the error for each failure.
2. The new or changed paths from `git status --short .agents .claude skills-lock.json`.
3. To commit those paths so teammates get the same set. After a clone, a teammate can restore from the lock file with `npx skills experimental_install`.
4. To restart the agent or reload skills if new skills do not show up.

Do not commit unless the user asks.

## Updating

To pull the latest version of every project skill:

```bash
npx -y skills update -p -y
```

To pick up changes to the set itself (skills added or removed here), run `npx -y skills update -p -y` first so this skill is current, then rerun Step 2.

## Changing the set

Edit [The set](#the-set) and the Step 2 commands together; they must list the same skills. Prefer a library's official skill repo; use a community skill only when no official one exists, and say so in the table.
