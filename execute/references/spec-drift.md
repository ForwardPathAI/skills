# Spec drift

The lead reconciles drift before dispatch and whenever the executor reports a mismatch. A changed file is a reason to inspect its behavior. Reconciliation updates references and accounts for existing work while preserving the requested outcome.

This procedure replaces generic stale-code, excerpt-mismatch, and path-whitelist stops in the current approved brief only for verified equivalents, regardless of when the source spec was written. Explicit exclusions and task-specific STOP conditions in the current approved brief remain binding unless an approved spec amendment explicitly supersedes them.

## Verify the current equivalents

Read the current approved goal, requirements, done criteria, and exclusions, including any approved spec amendments. Use relevant diffs, rename history, symbol searches, callers, and tests to establish where each referenced responsibility lives now. Read the current implementation before accepting a proposed mapping.

- Map moved files, renamed symbols, and extracted code to their current owners. Include only the successor files needed for the original task. An explicitly excluded file stays excluded even if it now owns that responsibility.
- Treat edits to an existing file as compatible only after checking that the original change still applies to its current contracts and behavior.
- Replace an obsolete verification command only when the current command exercises the same required behavior and retains the original expected result and coverage. A passing narrower test is insufficient.
- Verify already-implemented requirements against the task's start commit and the done criteria. Distinguish existing behavior from the executor's new changes. Record satisfied criteria, execute the remaining work, and rerun all criteria after implementation. If all criteria held before this task's implementation, report ALREADY SATISFIED instead of creating a duplicate change or PR.

**Done when:** each affected reference has a verified current equivalent, and each acceptance criterion is accounted for as already satisfied or remaining. Unproven equivalence is an unresolved gap.

## Record the amendment

Append a reconciliation amendment to the execution brief, preserving the source spec and its approved amendment record. Record:

- The reviewed commit and original spec identifier or path, including its stamped commit when present.
- Old-to-current file, symbol, and command mappings, with code/history/test evidence for each. Record compatible edits even when the path stayed the same.
- The complete resolved in-scope file list. Keep explicit exclusions intact.
- Any generic stale-reference STOP condition superseded by a verified mapping, so the executor can apply the mapping alongside the current approved spec.
- Every done criterion, its current verification command and expected result, and evidence for anything already satisfied.
- Remaining implementation work and a statement that the goal, contracts, acceptance meaning, and task-specific STOP conditions are unchanged.

For example: `src/orders.ts` was split into `orders/service.ts` and `orders/routes.ts`; the requested validation now belongs in `orders/service.ts`. Cite the extraction commit and current caller/test evidence, then list the resolved files and verification commands.

Continue autonomously once those claims are verified. Include the current approved spec, its amendment record, and the reconciliation mapping in the executor's context, and summarize the amendment in the PR and final report. A later amendment replaces its earlier mapping while preserving the evidence trail. Executor resumption is a Step 3 REVISE round.

**Done when:** the brief contains a complete, evidence-backed scope and verification mapping that the executor and reviewer can use without this conversation.

## Propose unresolved requirement changes

Follow [Propose and approve a spec amendment](../SKILL.md#propose-and-approve-a-spec-amendment) when proceeding would require a new product behavior, a changed contract, weaker acceptance criteria, work beyond verified successors, or crossing an explicit exclusion. Use the same procedure when code and history cannot establish an unambiguous mapping, or a task-specific STOP condition holds.

Preserve completed work and present the affected requirement, evidence, and exact proposed source edit. Reconciliation alone preserves requirements; user approval authorizes the named requirement change and source update. Refresh the execution brief from the revised source, or record an approved amendment with the source update pending when editing is unavailable, as that procedure specifies.
