---
name: effort-estimate
description: Estimate engineering effort in hours for a feature, workstream, or software build. Use when the user asks how long a piece of work will take, wants cost or timeline derived from engineering hours, or when another skill needs a reusable effort breakdown.
---

# Effort Estimate

Produce a bottom-up point estimate of developer effort. Treat it as a scope model, not a promise of elapsed time: state what the number covers and expose estimate-changing uncertainty instead of hiding it in contingency.

## Step 1: Set the estimation contract

Determine from the request and available context:

- the scope boundary: a feature, workstream, or production-ready build;
- the unit, defaulting to developer hours;
- what delivery work the estimate includes and excludes;
- the rate or developer capacity, only when cost or calendar time is requested.

If inputs are missing, proceed with explicit assumptions rather than turning estimation into a required interview. For a ForwardPath custom build, fixed-price estimate, engineering report, or SOW input, read and apply [references/forwardpath-delivery.md](references/forwardpath-delivery.md).

This step is complete when the scope boundary, inclusions, exclusions, and any values needed for cost or timeline calculations are explicit.

## Step 2: Build the coverage ledger

Read all provided requirements and artifacts. When estimating changes to an accessible codebase, inspect the relevant implementation, tests, dependencies, and delivery path before assigning hours.

Map every requested capability to one or more work items. Add enabling or cross-cutting work only when it is required to deliver the requested outcome, and label the reason. Do not invent optional features. Record missing details as assumptions.

This step is complete when every requested capability is accounted for exactly once and every added work item traces to delivery of that capability.

## Step 3: Estimate bottom-up

Break the ledger into work items small enough to estimate independently. Assign each a point estimate based on its implementation work, integration boundaries, ambiguity, edge cases, and verification burden.

- Focus hours on ambiguity and edge cases, not boilerplate.
- Include task-specific developer testing; do not add it again as a blanket percentage.
- Do not add a generic contingency percentage. Represent uncertainty through assumptions, confidence, and price levers.
- Avoid false reuse: credit existing components only after confirming that they fit the requested behavior.
- Keep effort and duration separate. Parallelism or part-time allocation changes calendar time, not total hours.

This step is complete when every ledger item has one point estimate and the estimates contain no blanket padding or double counting.

## Step 4: Isolate price levers

A **price lever** is a decision or unknown whose plausible answers materially change the total. For each one, state:

- the assumption used in the baseline;
- why the alternative changes the work;
- the estimated hours delta or scenario totals;
- High, Medium, or Low impact, ordered highest first.

Omit questions that only clarify implementation without moving the estimate. Continue under the stated baseline unless no defensible estimate is possible or the calling skill requires a confirmation gate.

This step is complete when every material unknown is either fixed by a stated assumption or represented by a quantified price lever.

## Step 5: Audit and present

Check that the line items sum to the stated total, all requested scope is covered, exclusions are not priced, and unusually low or high items have a defensible basis.

Return hours by default:

| Work item | Hours | Basis |
|---|---:|---|
| [Concrete delivery item] | [Point estimate] | [Scope or assumption driving the number] |
| **Total** | **[Sum]** | |

Follow the table with assumptions, exclusions, confidence, and price levers only when they add information. Calculate cost or calendar time only when requested or required by the calling skill, using the contract from Step 1. Keep the baseline as a point estimate; use ranges for alternative price-lever scenarios.

The estimate is complete when every requested capability appears in the audited breakdown and every reported total can be reproduced from the shown numbers.
