---
name: setup-fp-skills
description: Set up the Forward Path skill kit and route the current request to the relevant skill. Use when asked to set up FP skills, when beginning work in a Forward Path product repo, or when another skill needs this roster.
---

# Setup FP skills

Use this roster to select skills for the current request. Read a selected skill when its work begins, and follow its instructions. Keep reusable procedures in their owning skills.

## Roster

Prefer a specific workflow match over a general one. For example, a dependency-security sweep uses security-sweep, which calls pr-open at its publishing step; it does not start by opening a PR.

| Skill | When | Install if missing |
|---|---|---|
| unslop | Every reply | `npx skills add https://github.com/cursor/plugins --skill unslop` |
| domain-modeling | Terminology, `CONTEXT.md`, or an ADR | `npx skills add https://github.com/mattpocock/skills --skill domain-modeling` |
| grill-with-docs | Sharpening a plan or design; also needs grilling | `npx skills add https://github.com/mattpocock/skills --skill grill-with-docs` and `--skill grilling` |
| [issue-writer](../issue-writer/SKILL.md) | Drafting, creating, or updating an issue | `npx skills add forwardpathai/skills/issue-writer` |
| [ticket-refiner](../ticket-refiner/SKILL.md) | Resolving missing intent in an existing issue | `npx skills add forwardpathai/skills/ticket-refiner` |
| [linear-backlog-grill](../linear-backlog-grill/SKILL.md) | Reviewing and refining a backlog | `npx skills add forwardpathai/skills/linear-backlog-grill` |
| [pr-open](../pr-open/SKILL.md) | Opening or updating an ordinary or stacked PR | `npx skills add forwardpathai/skills/pr-open` |
| [security-sweep](../security-sweep/SKILL.md) | Fixing Dependabot alerts across repositories | `npx skills add forwardpathai/skills/security-sweep` |
| [prototype](../prototype/SKILL.md) | Building a prototype from a SOW | `npx skills add forwardpathai/skills/prototype` |
| [azure-infra-setup](../azure-infra-setup/SKILL.md) | Azure infra, Terraform, Bicep, Container Apps, ACR, Key Vault | `npx skills add forwardpathai/skills/azure-infra-setup` |
| [customer-deployment-package](../customer-deployment-package/SKILL.md) | A customer deployment handoff or client install docs | `npx skills add forwardpathai/skills/customer-deployment-package` |

Other installed skills remain available through the session's skill catalog. This roster is a starting point, not a requirement to use a listed skill for every request.

## 1. Select the next skill

Apply unslop to the response. If the user only asked to set up FP skills, load that baseline, report that routing is ready, and stop. Do not load or install the rest of the roster for a setup-only request.

For a concrete task, select the matching workflow and identify its next needed dependency. Read dependencies at the step that needs them, not all at the beginning. For a multi-stage task, finish the current stage before loading the next stage's skill.

Complete when the next skill and its purpose are clear from the request.

## 2. Resolve and read only selected skills

For a selected skill, use the session catalog's path when available. Otherwise search in order:

1. Sibling of this skill: `../<name>/SKILL.md`.
2. Current repo: `.agents/skills/<name>/SKILL.md`, `.cursor/skills/<name>/SKILL.md`, `.claude/skills/<name>/SKILL.md`.
3. User roots: `~/.agents/skills/<name>/SKILL.md`, `~/.claude/skills/<name>/SKILL.md`, `~/.cursor/skills/<name>/SKILL.md`, `~/.codex/skills/<name>/SKILL.md`.

For grill-with-docs, also resolve grilling when that workflow is selected. If a selected skill is missing and installation is authorized, run its listed install command and search again. If it remains unavailable, report that dependency and continue any independent work. An unrelated missing skill does not block the task.

Read the resolved `SKILL.md`, unless it is already in context. Do not invent a missing skill's instructions or substitute a summary for its procedure.

Complete when the selected skill is read or its missing dependency is reported.

## 3. Run and return

Pass the selected skill the task context, existing artifact IDs, relevant evidence, requested mode, and any approval already obtained. Follow its completion criteria. Reuse its returned result instead of repeating its work or external writes.

A route does not authorize unrelated actions. Honor the user's scope and each workflow's applicable review gates. Report the result or remaining blocker once the user's requested work is complete.
