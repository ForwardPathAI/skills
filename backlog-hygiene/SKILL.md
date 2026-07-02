---
name: backlog-hygiene
description: Scan a Linear project's backlog for relevance — flag issues that are stale, already shipped, or duplicated — using update age, code/PR evidence from the repo, and similarity to other tickets, then apply confirmed actions one ticket at a time.
disable-model-invocation: true
---

# Backlog Hygiene

Answer one question per ticket: **is this still real?** Not whether it's well-specified or agent-suitable (that's [cloud-agent-triage](../cloud-agent-triage/SKILL.md)) — whether it still reflects work that needs doing.

Every ticket gets exactly one **verdict**:

| Verdict | Means | Default suggested action |
|---|---|---|
| **Keep** | Still relevant, no contrary evidence | None (see [thin-spec flag](#thin-spec-flag) below) |
| **Stale** | No update and no recent activity within the age threshold, no evidence it's done | Ping for relevance, deprioritize, or close |
| **Likely done** | Repo/PR evidence the work already shipped | Comment with evidence, move to a completed/canceled state |
| **Duplicate or superseded** | Same scope as another issue, or a newer issue replaces its intent | Link and close the redundant one |

This skill is **read-only until Step 6** — gathering evidence and reporting never writes to Linear. Every write is gated behind an explicit, per-ticket confirmation.

## Prerequisites

- Run from the target git repository (Step 3's code-evidence check searches it).
- Linear MCP available, authenticated for the workspace.
- `gh` authenticated — optional, sharpens the code-evidence check against merged PRs; falls back to `git log` alone if missing.

Stop and tell the user what's missing if the Linear MCP is unavailable.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Resolve project
- [ ] Step 2: Collect candidate issues
- [ ] Step 3: Gather evidence per issue
- [ ] Step 4: Assign a verdict
- [ ] Step 5: Report
- [ ] Step 6: Apply confirmed actions
```

### Step 1: Resolve project

Infer the Linear project from the repo name or git remote (as [issue-writer](../issue-writer/SKILL.md) does), then confirm with the user before scanning. Use their project/team name directly if they named one — no confirmation needed.

### Step 2: Collect candidate issues

`list_issues` filtered to the resolved `project`, paginating with `cursor` until `hasNextPage` is false. Exclude terminal issues: read each status's `type` via `list_issue_statuses` and skip `completed`/`canceled` — never filter by display name (a team's "Done" column may not be the only completed-type state).

### Step 3: Gather evidence per issue

Fetch in parallel when there are many candidates. For each issue, collect:

| Evidence | How |
|---|---|
| **Age** | Days since `updatedAt`. Default stale threshold: **90 days**. Use a tighter/looser threshold if the user names one. |
| **Activity** | `list_comments` (`issueId`) — any discussion at all, how recent, and whether the newest comment is within the stale threshold. |
| **Code/PR evidence** | Pull concrete nouns from the title/description (file names, component names, feature names) and `Grep`/`Glob` the repo for them. Then `git log --all --grep="<issue-identifier>"` and, if `gh` is available, `gh pr list --state merged --search "<issue-identifier>"` — teams commonly reference the Linear ID in commits or PR titles. Record the specific file, commit, or PR found; "found nothing" is also evidence. |
| **Duplicate/superseded** | `list_issues` with `query` set to the issue's key terms, scoped to the same `project`. Compare scope, not just title wording — a near-identical newer issue supersedes an older one even with a different title. |

A vague signal ("might be related") is not evidence — only record a finding you can cite (a file path, a commit SHA, a PR link, another issue's identifier).

### Step 4: Assign a verdict

Apply in this order — first match wins:

1. Found a same-scope issue (duplicate) or a newer issue that replaces this one's intent (superseded) → **Duplicate or superseded**
2. Found code/PR evidence the described work already shipped → **Likely done**
3. No update past the age threshold **and** no recent activity within that threshold **and** neither of the above → **Stale**
4. Otherwise → **Keep**

#### Thin-spec flag

On a **Keep** verdict, separately check whether the description would pass [issue-writer](../issue-writer/SKILL.md)'s "before submitting" bar (real file paths, measurable acceptance criteria, explicit scope). If it wouldn't, attach a one-line flag naming the missing or thin sections: *"spec is thin — consider running ticket-refiner; gaps: Technical Context, Acceptance Criteria"*. This is a note, not a verdict change, and never triggers a write on its own.

### Step 5: Report

```
Backlog hygiene for <project> (<N> issues scanned):

Duplicate or superseded (<k>)
| Issue | Last updated | Evidence | Suggested action |
|-------|--------------|----------|-------------------|

Likely done (<k>)
| Issue | Last updated | Evidence | Suggested action |
|-------|--------------|----------|-------------------|

Stale (<k>)
| Issue | Last updated | Evidence | Suggested action |
|-------|--------------|----------|-------------------|

Keep (<k>) — <m> flagged thin-spec
| Issue | Last updated | Thin-spec gaps | Suggested action |
|-------|--------------|----------------|-------------------|
```

Link each issue with its Linear URL. Cite the evidence column with what you actually found (commit SHA, PR link, file path, other issue id) — not a restated verdict.

### Step 6: Apply confirmed actions

Walk the non-Keep groups one ticket at a time. For each, present the evidence and a short action menu, and wait for an explicit choice before calling any write tool — never batch-apply:

| Verdict | Action menu |
|---|---|
| Duplicate or superseded | Link via `duplicateOf` (true duplicate) or `relatedTo` (superseded but distinct) + comment + close; or comment-and-link only; or skip |
| Likely done | Move to a `completed`-type state + comment citing the evidence; or comment only, asking the owner to confirm; or skip |
| Stale | Comment pinging for a relevance check; or close (`canceled`-type state) + comment; or lower priority; or skip |

For thin-spec flags on **Keep** tickets, offer to read and follow [ticket-refiner/SKILL.md](../ticket-refiner/SKILL.md) on that issue now, or leave it for later.

Resolve target state names via `list_issue_statuses` (`statusType`, never a guessed display name). Before applying a label like "stale" or "duplicate", check `list_issue_labels` for an existing match — apply it if present, otherwise skip the label and rely on the comment; never invent a label.

## Decision table

| Situation | Action |
|---|---|
| Repo has no commits/PRs referencing Linear IDs | Fall back to the keyword `Grep`/`Glob` search only; note that the identifier search found nothing. |
| Issue is mid-cycle with recent comments but old `updatedAt` | Activity beats age — not Stale. |
| Issue has comments, but none within the stale threshold | Old discussion alone does not beat age — it can still be Stale. |
| Two issues look like duplicates but scopes differ on inspection | Not a duplicate — leave both as Keep (or flag thin-spec if either is vague). |
| User wants a different age threshold | Use theirs for Step 3; state the threshold used in the report. |
| `gh` unavailable | Skip the merged-PR search; rely on `git log --all --grep` and the keyword search. |

## Anti-patterns

- Writing to Linear during Steps 1–5 — evidence-gathering and reporting are read-only.
- Calling `save_issue`/`save_comment` for more than one ticket without a confirmation in between.
- Treating "no comments" alone as Stale — pair it with the age threshold, not either signal alone.
- Closing a ticket on "likely done" without citing the specific file/commit/PR that proves it.
- Inventing a label or state name instead of resolving it via `list_issue_labels`/`list_issue_statuses`.
- Confusing this skill's relevance verdicts with [cloud-agent-triage](../cloud-agent-triage/SKILL.md)'s suitability verdicts — a Keep ticket can still be "Not a fit" for an autonomous agent, and a thin-spec ticket isn't automatically Stale.

## Additional resources

- Rewriting a thin-spec ticket: [ticket-refiner/SKILL.md](../ticket-refiner/SKILL.md)
- Agent-ready description template and bar: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
- Whether a (relevant) ticket suits an autonomous cloud agent: [cloud-agent-triage/SKILL.md](../cloud-agent-triage/SKILL.md)
