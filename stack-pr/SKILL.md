---
name: stack-pr
description: Compatibility entry point for a stacked Linear-linked GitHub PR. Use when the user invokes stack-pr; pr-open owns the shared workflow.
---

# Stack PR

Read and follow [pr-open](../pr-open/SKILL.md) with `mode=stacked` and `tracking=required`. Pass through the user's repository, base, existing issue/PR, scope, and verification results. Let the shared skill capture the parent before changing branches.

If the sibling is absent in a single-skill install, locate `pr-open` in the available skill catalog or installed skill roots. If missing, install it with `npx skills add forwardpathai/skills/pr-open` when installation is authorized, then read it. Report an unresolved dependency rather than recreating the workflow here.

Return the shared skill's PR result, including the head and base. This entry point owns no Git or Linear procedure.
