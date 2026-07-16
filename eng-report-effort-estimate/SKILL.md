---
name: eng-report-effort-estimate
description: Generate the combined Engineering Report + Effort Estimate document in Notion for a ForwardPath custom-build project — the pre-SOW internal doc that breaks technical effort into hours and price. Use when the user asks to scope a client build, estimate effort or hours, create an engineering report or scoping doc, or provides a discovery-call transcript or client requirements wanting engineering analysis.
---

# Engineering Report + Effort Estimate

Generate the internal scoping and effort-estimation document for a ForwardPath custom build. Sales, Engineering, and Client Success all read this one document; it feeds directly into SOW pricing.

Two non-negotiables govern every step:

1. **Extract, don't invent.** Every feature, constraint, pain point, and requirement in the document must trace back to the provided context (transcripts, notes, RFPs, emails). Anything not discussed is marked TBD or raised as an open question — never fabricated.
2. **No silent phasing.** Never split features into V1/V2, defer anything to "future", or drop a feature to simplify a recommendation without explicit user approval. Every feature in the source material appears in the document unless the user says to exclude it. Phasing opportunities are presented as price levers in Step 0.3, not decided in the document.

A **price lever** is a question whose different answers change the hours/cost estimate. It is the only kind of question this skill asks — the document exists to understand price, not to perfectly scope the build, and every question put to the client risks going unanswered. The test: would a different answer move the number? If it only sharpens scope or picks an implementation detail with no effort delta, it doesn't belong.

## Step 0: Understanding check (gate)

Read ALL provided context — transcripts, scoping notes, requirements, RFPs, prior emails, attachments — and read [references/estimation-rules.md](references/estimation-rules.md) (needed to quantify price levers). Then produce for the user:

### 0.1 Build summary
2–3 plain-language sentences: what is being built and why, understandable with zero technical background.

### 0.2 What we're building (non-technical)
Every distinct feature, function, and capability discussed in the context, in plain language from the user's perspective. No jargon, no architecture.

> - The system will automatically read incoming purchase orders from email and extract key data
> - Users will see a dashboard showing all active jobs and their current status

### 0.3 Price levers
Every question that passes the price-lever test, each with a price-impact estimate. Keep the list lean.

| Question | Why it moves the price | Price impact |
|---|---|---|
| [The decision or unknown] | [What about it drives hours] | [Magnitude + range, e.g. **High: +15–25 hrs / +$8,250–$13,750**] |

- Impact = magnitude (**High / Medium / Low**) plus an hours-and-dollar range wherever one can be estimated. If it can't be quantified yet, say why and still give a rough magnitude.
- Where the answer swings between two concrete options, show both (e.g. "Phase 1 only: 60 hrs / $33,000 — Phase 1+2: 110 hrs / $60,500").
- Order by price impact, highest first.
- Phasing is a price lever: where features could split into phases, present the phase options with the price delta of each.

### 0.4 Standard add-ons
Read [references/add-ons.md](references/add-ons.md). Confirm each applicable baked-in default is in the estimate (or the user drops it); skip defaults whose Applies to condition is not met. Then propose each offered add-on whose trigger fits, priced in the 0.3 format. For each, the user decides: **build** (estimate as a feature), **offer** (list in the document's Optional Add-Ons section with its price), or **skip**.

**Gate: do not proceed until the user confirms the understanding check is accurate and has decided on each price lever — which to put to the client, and what assumption to use in the meantime so the estimate can still be produced — and on each proposed add-on.**

## Step 1: Collect required inputs

Verify you have the following. Ask for any missing Critical Input.

### Critical inputs (must have)

| Input | Where used |
|---|---|
| Client name | Header, throughout |
| Names of people on the scoping call | Header |
| Deployment target (Web App, Mobile, etc.) | Header, architecture |
| Authentication method (if discussed) | Header, architecture |
| Recording/transcript link | Header |
| Discovery call transcript or scoping notes | All sections |

### Nice-to-have inputs

| Input | Where used |
|---|---|
| Client-provided requirements or RFP | Sections 1, 3+ |
| Existing systems / tech stack info | Integration section |
| Client's cloud environment | Architecture decisions |
| Number of developers assigned | Effort calculation |
| Target completion date | Timeline section |

Defaults for anything not provided are in [references/estimation-rules.md](references/estimation-rules.md).

## Step 2: Create in Notion

Create the document as a new page in the Engineering Scoping Documents database.

- Data source ID: `26c92ad1-579b-80d5-b456-000bf5fac297`
- Before creating, fetch the Notion enhanced markdown spec: `notion://docs/enhanced-markdown-spec`

| Property | Value |
|---|---|
| Project Name | `[Client Name] - [Project Short Name]` |
| Type | `Engineering Scoping Doc` |
| Client Name | Client company name |
| Effort Estimate Required By | Date if provided, otherwise blank |
| Build Timeline Estimate | Calculated from effort (see estimation rules) |
| Point Consumption | Total estimated hours |

The database has "Engineering Scoping Doc" and "Engineering Effort Estimate" as separate types; this combined document uses "Engineering Scoping Doc". If the user wants a combined type added to the schema, handle that separately.

## Step 3: Write the document

Read [references/section-rules.md](references/section-rules.md) — it holds the required document structure, header and effort-table formats, per-section authoring rules, and style rules. Each technical section carries an inline effort estimate in the format given in [references/estimation-rules.md](references/estimation-rules.md).

## Step 4: Post-generation audit (gate)

Audit the finished document line-by-line against the original source material. Output the full audit to the user alongside the document; if issues were found and fixed, note what changed.

### 4.1 Coverage check
For every feature, function, integration, pain point, and requirement in the source context, confirm it appears in the document — no source item unaccounted for. Output a checklist:

> ☑ [Feature/requirement] — Found in Section X.X
> ☐ [Feature/requirement] — **MISSING** — Adding to Section X.X

Fix anything missing before presenting the final version.

### 4.2 Phasing check
Confirm no features were silently deferred or removed (non-negotiable 2). Anything the document excludes must appear in Open Questions as a price lever with the price delta of each phase option.

### 4.3 Effort sanity check
- Inline section totals roll up correctly to the summary table, and a QA Fixes line is present.
- Timeline math works: build weeks + internal QA phase in weeks (convert days ÷ 5 when the QA tier is in days) + 3 weeks UAT (see estimation rules).
- Flag sections with suspiciously low or high estimates for a second look.

### 4.4 Completeness check
- All mandatory sections present; header table fully populated (or TBD where appropriate).
- Access & Data Required section has everything the client needs to provide.

### 4.5 Price-lever check
- Every question in the document passes the price-lever test and meets every Step 0.3 rule (impact estimate, ordered highest first, lean list); remove any that don't.

### 4.6 Add-ons check
- Each applicable baked-in default is estimated or was explicitly dropped by the user; non-applicable defaults are omitted (not estimated, not treated as drops).
- Every "build" add-on is estimated like any feature; every "offer" add-on appears in Optional Add-Ons with hours and cost; none silently dropped.
