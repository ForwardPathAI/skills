---
name: open-pr
description: Open a Linear-linked GitHub PR through the shared pr-open workflow. Use when the user asks to open a PR or submit changes for review in this repository.
---

# Open PR

Read and follow the repository's canonical [pr-open](../../../pr-open/SKILL.md) skill with `mode=standard` and `tracking=required`. For an explicitly stacked request, use `mode=stacked`. Pass through the user's base, existing issue/PR, scope, and verification results.

The canonical skill owns issue tracking, branching, committing, pushing, and PR creation. Return its result without repeating any write. If this entry point has been copied outside this repository, resolve pr-open through the session skill catalog or installed skill roots; report a missing dependency rather than recreating its procedure.
