---
name: ticket-refiner
description: Resolve missing intent in a Linear issue through a focused interview, then draft or save a rewrite using issue-writer. Use for a vague ticket or when a backlog review supplies specific gaps to refine.
---

# Refine a ticket

Own the interview that resolves missing intent. [issue-writer](../issue-writer/SKILL.md) owns the issue template, repository evidence requirements, and issue writes.

## Inputs and modes

Require an issue ID or a supplied copy of the issue and discussion. Accept a caller's gap list, repository evidence, prior answers, and proposed split boundaries. Reuse them after checking they still apply.

- `draft`: interview and return proposed changes without any Linear write. Use when a caller owns the review and save step, or the user only requests a proposal.
- `save`: the standalone default for a request to refine an existing issue. Show the exact draft, obtain approval, then hand it to `issue-writer` in `update` mode.

Linear MCP is needed to fetch a ticket not supplied in context and for saving. A caller with complete issue/discussion context can use draft mode without it. Locate `issue-writer` through the sibling link or installed skill catalog; report a missing dependency rather than copying its procedure.

## 1. Load the ticket and find gaps

Read the issue, its relations, and prior comments. If the caller supplied current copies, reuse them. Read `issue-writer` and assess its actual description template and quality bar; do not maintain a second template here.

List only missing or vague requirements, scope, rationale, verification, dependencies, or implementation evidence. Resolve code facts by reading the repository before asking the user. Preserve already-concrete sections. If the ticket already meets the bar, return `unchanged` and its reason without an interview or write.

Complete when each gap has either evidence that resolves it or a specific unanswered question.

## 2. Interview only for unresolved intent

Ask one material question at a time, starting with the outcome and reason, then scope, acceptance, dependencies, and verification. Skip questions answered in the issue, discussion, caller's report, or repository.

Ask for a concrete outcome when an answer is vague. After one pushback on the same gap, record a still-unknown answer as an open question. Do not invent a requirement, file path, or metric.

For oversized work, resolve the smallest independently shippable slices using [issue-writer's splitting rules](../issue-writer/splitting.md). Each slice needs its own outcome, scope, and verification. Preserve unresolved blockers explicitly rather than declaring the ticket ready.

Complete when each gap is resolved or recorded as an open question with its effect on readiness.

## 3. Produce the draft

Call `issue-writer` in `draft` mode with the existing issue, resolved answers, repository evidence, and intended field changes. It returns the complete issue payload, or a split proposal with standalone issue drafts and a grouping-document draft. Use its template and quality bar without recreating either here.

Return the source issue ID, proposed fields and description, readiness verdict, unresolved questions, and a short explanation of changes. In draft mode, stop here: do not save, comment, or ask for a second approval that belongs to the caller.

## 4. Review and save

In save mode, show the exact proposed text and field changes. Once approved, call `issue-writer` in `update` mode for the source issue. Pass the approval and unchanged draft so the user is not asked again. If edits change the reviewed content, show the revised text before saving.

For an approved split, call `issue-writer` in `create` mode for the standalone replacements and grouping document, then in `update` mode for the source issue's agreed disposition and links. Record returned IDs so partial retries reuse saved work. Do not create sub-issues or close the source issue unless separately requested.

After successful writes, add one short Linear comment to the source issue explaining the refinement. On a retry, check whether that comment already exists before adding it again. Return saved issue/document URLs and unresolved questions. Finish one ticket or split set before interviewing the next.
