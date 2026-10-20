---
name: open-pr
description: Open Linear-linked GitHub PRs through the shared pr-open workflow, as one PR, a split, or a stack. Use when the user asks to open a PR, submit changes for review, split work into PRs, or stack a PR in this repository.
---

# Open PR

Read and follow the repository's canonical [pr-open](../../../pr-open/SKILL.md) skill with `tracking=required`. It chooses one PR, a split, or a stack; for an explicitly stacked request, start in `mode=stacked`. Pass through the user's base, existing issue/PR, scope, and verification results.

The canonical skill owns issue tracking, branching, committing, pushing, and PR creation. Return its result without repeating any write. If this entry point has been copied outside this repository, resolve pr-open through the session skill catalog or installed skill roots; report a missing dependency rather than recreating its procedure.
