---
name: open-pr
description: Compatibility entry point for opening Linear-linked GitHub PRs from local changes, including deciding between one PR, several independent PRs, or a stack of dependent PRs. Use when the user invokes open-pr or asks to open a PR, ship changes, or put work up for review — including "stack a PR", "stacked PR", "open a dependent PR", "stack this on top", "split this into PRs", or "branch on top of this". pr-open owns the shared workflow.
---

# Open PR

Read and follow [pr-open](../pr-open/SKILL.md) with `tracking=required`. It chooses one PR, a split, or a stack (Step 2), and uses `mode=stacked` for each dependent layer. For an explicit stack request, start in `mode=stacked`. Pass through the user's repository, base, existing issue/PR, scope, and verification results.

If the sibling is absent in a single-skill install, locate `pr-open` in the available skill catalog or installed skill roots. If missing, install it with `npx skills@1.7.4 add forwardpathai/skills/pr-open` when installation is authorized, then read it. Report an unresolved dependency rather than recreating the workflow here.

Return the shared skill's PR results, including each head and base. This entry point owns no Git or Linear procedure.
