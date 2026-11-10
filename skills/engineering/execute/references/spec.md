# Spec mode

A **spec** is a set of tickets joined by blocking relations: a Linear document from [issue-writer's splitting](../../issue-writer/splitting.md), a Linear project, or tickets the user lists. The tickets are not a list of steps but a **task graph**. The **frontier** is every open ticket whose blockers have all merged; it is always safe to start.

Each ticket still runs [Steps 1–8](../SKILL.md) and ships its own PR. Spec mode decides which tickets run, when, and in what order. Invoking execute on a spec authorizes that pipeline for every ticket in the graph, and nothing outside it.

## 1. Load the graph

- Read the spec document, if any, whole: its decisions and out-of-scope list bind every ticket.
- Collect the tickets: the document's Tickets table, the project's issues, or the user's list. Skip tickets whose status type is `completed` or `canceled` (`list_issue_statuses`; never guess from display names).
- `get_issue` with relations for each, and build the graph from `blockedBy`. A cycle, or a blocker outside the spec that hasn't merged, is a decision: ask.
- Tickets with an open PR already need no new executor: run Step 8 on that PR.
- A ticket that fails Step 1's readiness check is blocked, not run. A Linear project often holds unrefined backlog; report those tickets as needing ticket-refiner and treat them as blocked.

Report the graph and the first frontier to the user, then start. No approval needed.

Keep a progress file in your scratchpad (outside the repo): each ticket, its state (waiting, running, in review, armed, merged, already satisfied, blocked), its PR, and its ledger summary. It survives context compaction; Linear and GitHub remain the source of truth.

**Done when** every open ticket has a place in the graph and the frontier is known.

## 2. Explore once, if tickets share ground (optional)

When several tickets depend on the same unexplored code or docs, dispatch one exploration subagent to write markdown notes to a scratchpad folder outside the repo. Pass that path to each executor as a pointer instead of repeating the notes.

## 3. Run the frontier

1. For each frontier ticket, run Steps 1–3. Run executors in parallel, each in its own worktree from the current base tip, up to 3 at once unless the user named a limit. Run them in the background where the host allows.
2. Before landing an approved ticket, check whether the base moved since its executor started (another ticket merged). If so, REVISE: have the executor merge the new base tip into its branch and resolve conflicts, then re-run Step 3.
3. Land approved tickets one at a time, since Steps 4–8 use your checkout: run Steps 4–8, then return to a clean base (`git switch <base> && git pull --ff-only`) before landing the next. The Preflight checks hold again at that point; confirm them.
4. In Step 8, arm the PR. When the host can wake you on PR activity, keep auto-pilot-pr's watch and move on to the next ticket instead of ending the turn. When it can't, note the PR as armed and move on.

A blocked ticket doesn't stop the spec. Its dependents wait; independent tickets keep moving. Collect decisions and ask them together when nothing else can run.

**Done when** every frontier ticket is merged, armed, in review, already satisfied, or blocked.

## 4. Advance

A ticket joins the frontier when every blocker has **merged** or is **already satisfied** (the base holds that behavior). Armed or approved is not merged: the base doesn't hold the blocker's code yet.

On each wake (a merge, new review feedback, a failed check) on an open PR, check out its branch from a clean tree (`gh pr checkout <pr>`), run a new auto-pilot-pr pass, then return to a clean base. After any merge, pull the base, recompute the frontier, and dispatch newly ready tickets. End the turn only when nothing can run until a PR changes. If the host can't wake you, finish with the report below; running execute on the same spec again picks up where this run stopped.

Stack a ticket on its blocker's open PR only when the user asks. Then follow open-pr's stacking rules, and auto-pilot-pr arms only the bottom PR.

**Done when** every ticket is merged, already satisfied, or blocked.

## 5. Finish the spec

Once every ticket has merged, pull the base and check the spec's "Done when" criteria there. A failure is a new ticket: draft it with issue-writer and ask before creating it.

Report:

- A table of tickets: identifier, PR URL, state, and any decision asked.
- The spec-level "Done when" results, or what remains and why.
- Per ticket, the Finish items from [the main skill](../SKILL.md#finish) worth knowing; keep the rest in the progress file.
