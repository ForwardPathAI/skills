---
name: plan-refiner
description: Harden an existing Cursor plan so a weaker executor model can implement it without judgment calls — hunt every unknown, resolve it via codebase/web research or a one-gap-at-a-time user interview, anticipate non-obvious scenarios, and rewrite the plan file in place as unambiguous, verifiable statements. Use when the user says "refine this plan", "improve the plan", "harden the plan", "make this plan executor-ready", or hands over a plan file before delegating it to a cheaper model or agent.
disable-model-invocation: true
---

# Plan Refiner

A plan written by a strong model leans on judgment the reader is assumed to have. A weaker executor doesn't have it — it takes every "handle appropriately" literally and guesses at every unstated choice. This skill closes that gap: it turns a plan's implicit knowledge into explicit statements, decides the scenarios the author left unsaid, and rewrites the plan **in place** so a lesser model can execute it verbatim.

You have codebase access, internet search, and the user. Exhaust research before asking the user; ask the user only for decisions that are genuinely theirs to make.

## Prerequisites

- The plan file path (ask if not given — typical locations: the path the user references, `.cursor/plans/`, or a workspace markdown file).
- Read access to the codebase the plan targets. If it isn't reachable, verify what you can and flag the rest as unverified.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Load the plan and its context
- [ ] Step 2: Hunt unknowns
- [ ] Step 3: Resolve by research first
- [ ] Step 4: Interview for the rest
- [ ] Step 5: Think ahead (adversarial pass)
- [ ] Step 6: Rewrite in place for a lesser executor
- [ ] Step 7: Report what changed
```

### Step 1: Load the plan and its context

Read the whole plan file. Then read every file, path, symbol, and doc it cites — you cannot judge whether a reference is correct without looking. Note the plan's intent and any verbatim user requirements; these must survive the rewrite unchanged.

### Step 2: Hunt unknowns

Scan for anything an executor would have to guess. Classify each into this taxonomy so nothing slips through:

| Kind | What it looks like |
|---|---|
| Vague directive | "handle appropriately", "add proper error handling", "refactor as needed", "etc." |
| Unverified reference | a file path, function, API, or config key asserted but not confirmed to exist |
| Open choice | "either X or Y", "consider using", a library/version left unpicked |
| Missing definition | undefined bar ("works well", "fast"), unstated data shape, unnamed command/environment |
| Implicit ordering | steps whose dependency order isn't stated |

### Step 3: Resolve by research first

Before asking anyone anything, resolve what you can:

- **Verify every cited path/symbol** against the actual codebase (grep/read). Replace wrong ones; add line-level anchors (`path/to/file.ts:45-67`) where they help the executor find the spot.
- **Web-search external facts**: current library APIs, version constraints, breaking changes, and known pitfalls of the chosen approach.
- **Convert each resolved unknown into a declarative statement**, never a suggestion: not "consider pdfplumber" but "Use `pdfplumber` 0.11 — already pinned in `requirements.txt`".

### Step 4: Interview for the rest

Some unknowns are genuinely the user's call: product trade-offs, priorities, irreversible or high-blast-radius choices. For those, interview the user **one gap at a time** — never dump the whole list at once. Push back once on a vague answer; if it's still vague, record it as an explicit **Open question** in the plan rather than inventing a decision.

Do not ask the user anything research in Step 3 could have answered.

### Step 5: Think ahead (adversarial pass)

Enumerate the non-obvious scenarios the plan doesn't mention and decide each one explicitly. Run the plan through these lenses:

- empty / zero / null / huge inputs
- first-run vs. repeat-run; idempotency and re-entrancy
- partial failure, retries, and cleanup on error
- concurrency and race conditions
- migrations, rollback, and backwards compatibility
- what happens to existing data and users when the change lands
- auth / permissions edge cases
- timezone, locale, encoding
- rate limits, timeouts, and offline behavior

For each lens **that applies**: write the expected behavior into the plan. For each that doesn't: skip it silently — do not pad the plan with "N/A" entries.

### Step 6: Rewrite in place for a lesser executor

Rewrite the same plan file (do not spawn a new document) with these executor-friendly properties:

- Numbered steps in strict dependency order, each with concrete file paths and exact commands to run.
- Decision rules instead of judgment: "if the test fails with `X`, do `Y`" — never "use your judgment".
- A **Verification** line per milestone: the exact command plus its expected output.
- Explicit sections: **Assumptions** (every decision made during refinement, so the executor never re-litigates them), **Out of scope**, and **Open questions** (unresolved user-owned gaps).
- Preserve the original intent and any verbatim user requirements.

### Step 7: Report what changed

Summarize for the user: unknowns resolved (and how), scenarios added, and questions asked. The file is already saved — this is a report, not an approval gate.

## Decision table

| Situation | Action |
|---|---|
| Plan is already fully concrete and verifiable | Say so; don't rewrite for the sake of it. |
| A cited path/symbol doesn't exist | Search for the intended target; fix it, or flag it as an Open question if you can't find it. |
| User gives a vague answer twice on the same gap | Record it as an Open question; stop pushing. |
| Plan targets a codebase not reachable from here | Verify what you can; mark unverifiable references explicitly rather than assuming them correct. |
| An unknown is a reversible implementation detail | Decide it yourself, research-backed, and log it under Assumptions — don't interrupt the user. |
| An unknown is irreversible or high-impact | Interview the user before deciding. |

## Anti-patterns

- Rewriting a suggestion into another suggestion ("consider…" → "you might…") instead of a decision.
- Inventing a file path, function name, or command you didn't verify.
- Padding the plan with inapplicable edge cases just to look thorough.
- Asking the user something a grep or web search would have answered.
- Dumping every interview question at once instead of one gap at a time.
- Dropping the original plan's intent or verbatim requirements during the rewrite.

## Executor-readiness bar

Before finishing, the rewritten plan must pass — the test is that a weaker model could execute it with no judgment calls:

- [ ] No vague verbs ("handle", "improve", "refactor as needed") without a concrete target.
- [ ] Every file path and symbol is verified against the codebase, or explicitly flagged unverified.
- [ ] Every open choice is decided — library, version, approach — with the reason stated.
- [ ] Every step is in dependency order and has an exact command.
- [ ] Every milestone has a Verification line with expected output.
- [ ] Applicable edge-case scenarios are handled; the rest are out of scope by omission.
- [ ] Assumptions, Out of scope, and Open questions sections are present.

## Additional resources

- Producing agent-ready specs and the bar they must pass: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Interviewing a human to fill gaps, one at a time: [ticket-refiner/SKILL.md](../ticket-refiner/SKILL.md)
- After refining, pack the plan's codebase context into images for the executor: [plan-context-imager/SKILL.md](../plan-context-imager/SKILL.md)
