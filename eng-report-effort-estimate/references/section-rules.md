# Section Rules

## Document structure

Fixed structure — every section below must be present:

```
[Header Table]
---
Effort Summary Table (top-level — hours, cost, timeline at a glance)
---
1. Executive Summary
   1.1 Context
   1.2 Problem We're Solving
   1.3 Key Constraints & Implementation Challenges
   1.4 Options Discussed (if applicable)
   1.5 Expected Outcomes
2. Solution Overview
   2.1 System Components (data flow diagram)
   2.2 Core Capabilities
   2.3 Effort Estimate — Solution Architecture (inline)
3+ Technical Detail Sections (dynamic, based on solution)
   [Each section]:
   - What we learned from the call
   - Recommended approach
   - Alternatives considered
   - Limitations or risks
   - Effort Estimate — [Section Name] (inline)
[N+1] Integration Considerations
   - Effort Estimate — Integrations (inline)
[N+2] Optional Add-Ons (only when the user chose to offer add-ons — each labeled
      as a ForwardPath proposal, with hours + cost)
[N+3] Open Questions & Decisions Required
[N+4] Access & Data Required to Start Building
[N+5] Unresolved Questions for Follow-Up
---
Effort Summary — Full Breakdown (detailed table, bottom of doc)
```

## Header table

Notion table at the top of the document:

| Field | Value |
|---|---|
| Client Name | [Client Name] |
| Type | Engineering Report + Effort Estimate |
| Scoped With | [Names from call] |
| Deployment Target | [Web App, Mobile, etc.] |
| Authentication | [SSO type or TBD] |
| Recording Link | [Link or TBD] |
| Date | [Date of document creation] |

## Effort summary table (top of document)

Immediately after the header — the quick view for Sales and leadership:

| Component | Estimated Hours | Estimated Cost (CAD) | Notes |
|---|---|---|---|
| [Component 1] | XX hrs | $XX,XXX | |
| [Component 2] | XX hrs | $XX,XXX | |
| ... | | | |
| QA Fixes | XX hrs | $XX,XXX | Judged from complexity; QA review itself unbilled |
| **Total Build** | **XX hrs** | **$XX,XXX** | |
| **Internal QA phase** | — | — | X days/weeks, sized by complexity tier |
| **UAT (3 weeks minimum)** | — | — | Client-led |
| **Estimated Timeline** | **XX weeks** | | Build weeks + QA phase + 3 wks UAT, 1 dev at 2.5 hrs/day |

## Authoring rules

- **Capture client skepticism.** If the transcript shows the client expressing doubt, concern, or pushback about a feature or approach, note it — valuable context for the team.
- **Capabilities AND limitations.** When recommending an approach, state what it can and can't do. Don't oversell.
- **Decisions vs recommendations.** Label items the client confirmed **(Confirmed)** and items ForwardPath is proposing **(Recommended — pending client confirmation)**.
- **No redundancy across sections.** The top Effort Summary is the rollup; inline per-section estimates are the detail. Executive Summary is business context; Technical Detail sections are implementation context. Each section has one distinct purpose.
- **Tables over paragraphs.** Repeating patterns (options, features, effort lines, integrations) go in tables; prose is for narrative context only. Options compare as Approach | Description | Pros | Cons.
- Only price levers appear in Open Questions & Decisions Required and Unresolved Questions for Follow-Up; every question carries its price-impact tag — **(High impact)** / **(Medium impact)** / **(Low impact)** — with an hours/dollar range where one can be given.

## Formatting

- Numbered lists for sequential/prioritized items; bullets for non-sequential.
- ASCII diagrams for system component flows (Source → Processing → Delivery).
- Confidence levels or severity ratings where relevant.
- Checkboxes (☐) for the requirements checklist in Access & Data Required.
