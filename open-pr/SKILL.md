---
name: open-pr
description: Compatibility entry point for opening a Linear-linked GitHub PR. Use when the user invokes open-pr; pr-open owns the shared workflow.
---

# Open PR

Read and follow [pr-open](../pr-open/SKILL.md) with `mode=standard` and `tracking=required`. Pass through the user's repository, base, existing issue/PR, scope, and verification results. For an explicitly stacked request, use `mode=stacked` instead.

If the sibling is absent in a single-skill install, locate `pr-open` in the available skill catalog or installed skill roots. If missing, install it with `npx skills add forwardpathai/skills/pr-open` when installation is authorized, then read it. Report an unresolved dependency rather than recreating the workflow here.

Return the shared skill's PR result, including the head and base. This entry point owns no Git or Linear procedure.
