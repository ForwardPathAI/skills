# Branch handling

Record the source branch and HEAD, the base ref and its resolved commit, intended commits, and dirty paths before checkout. Inspect local and remote branch existence separately; a failed fetch can mean an authentication or network error, not an absent branch.

## Standard

Use the explicit base or resolve the repository default. Fetch that base and create the target branch from its remote tip. If the target already exists locally or remotely, inspect it and reuse it only when it belongs to this work.

If the source has committed work ahead of the base, identify the intended commits before checkout and carry over only those not already present on the target, in dependency order. Do not blindly cherry-pick every commit ahead when the source includes another feature. Preserve merge history when necessary rather than assuming every commit can be cherry-picked. Reuse an already-correct branch without rebuilding it.

## Stacked

Use the explicitly named parent, or capture the current non-default branch and its tip before creating the child. If the user asks to stack while on the default branch without naming a parent, resolve which parent they mean before proceeding. Do not silently turn it into a standard PR.

When the parent is current, create the child from the captured parent tip; uncommitted changes carry over. Existing parent commits stay on the parent and must not be cherry-picked into a separate history. When another parent is named, create from its verified tip and carry over only the intended child changes and commits that are absent from that parent.

If resuming an existing child PR, use that PR's verified base as the parent rather than treating the child itself as a new parent. Inspect an existing target branch before reusing it.

Before publishing the child, ensure the remote parent contains the intended parent tip. If it exists only locally, push that parent first. A non-fast-forward rejection needs resolution, not a force push. The PR base must be the parent, not the repository default.

## Prepared

Verify that the checked-out branch is the exact branch supplied by the caller. Keep its name, ancestry, and allowed-path constraints. Do not rebranch, rename it to a Linear branch, cherry-pick its history, or change the base chosen by the caller. Inspect the diff against that base before committing.

This mode supports security branches, SDK version-bump branches, and existing PR updates. Tracking remains a separate explicit input.

## Dirty worktrees and conflicts

Avoid stashing when checkout can preserve the working tree. When stashing is necessary, include untracked files with `git stash push -u`, give this operation a unique marker, and record its stash ref. Restore that exact stash after transferring commits. Do not pop an unrelated user's stash.

On a conflict, preserve the source commits and stash, report the conflicted files, and resolve only within the task's scope. Do not discard work, force checkout, or continue to publish an unresolved tree. Verify the original dirty work is accounted for after checkout and restoration, including unrelated changes left uncommitted.
