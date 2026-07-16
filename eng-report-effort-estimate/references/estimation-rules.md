# Effort Estimation Rules

## Baselines and defaults

| Parameter | Value |
|---|---|
| Rate | **$550/hour (CAD)** |
| Pricing model | **Fixed price** — this estimate becomes the SOW price; overruns are ForwardPath's to absorb |
| Standard monorepo setup (auth, DB, web app, API, queues, CI/CD) | **10 hours** — the only standard component baseline; everything else is estimated per-project from judgment |
| Developers | **1 developer** — multi-dev builds are rare and handled ad hoc when they come up |
| Dev capacity | **2.5 hours/day** = this project's share of a dev who splits across multiple client projects |
| Contingency | **None** — point estimates, no buffer %; uncertainty is handled through price levers in Step 0, not padding |
| Cloud | **Azure with Azure Foundry AI resources** unless client specifies otherwise |
| Authentication (undiscussed) | TBD |
| Recording link (not provided) | TBD |

## What dev hours include and exclude

**Included** in section estimates:
- Deployment / DevOps (CI/CD beyond the 10-hr setup, prod deploys, client-environment infra)
- Design / mockups (UI design passes before implementation)
- Dev self-testing
- UAT bugfix cycles (no separate UAT line)

**Excluded** (not estimated, not billed as dev hours):
- Client meetings / PM overhead
- Data migration, user documentation, training
- QA reviewer time (internal, unbilled — see QA phase below)

## Estimation principles

- Focus hours on **ambiguity and edge cases**, not boilerplate.
- AI-assisted engineering — estimates reflect aggressive but realistic timelines.
- Enterprise-grade: build for scale and maintainability.
- Non-Bun/TypeScript/Next.js apps may need additional setup time beyond the 10-hour baseline.

## Internal QA phase

Before the app goes to the customer for UAT, ForwardPath runs an internal QA pass: QA reviews, provides feedback, devs resolve issues.

- **Duration** (calendar time, added to the timeline) — size by app complexity:

| App complexity | QA phase |
|---|---|
| Simple (1–2 core flows, no integrations) | 2–3 days |
| Medium (several flows, 1–2 integrations) | 1 week |
| Complex (many flows, 3+ integrations, AI pipelines) | 2 weeks |

- **QA fix hours** (billed dev hours) — judged per project from complexity and risk; appears as its own line in the effort tables. QA reviewer time itself is never billed.

## Timeline calculation

```
Build:  total dev hours ÷ 2.5 hrs/day = working days ÷ 5 = build weeks
+ Internal QA phase in weeks (from complexity table above — if the tier is in days, convert: days ÷ 5)
+ UAT: minimum 3 weeks, client-led
= Estimated Timeline (weeks)
```

## Inline effort format (per technical section)

At the bottom of each technical section:

> **Effort Estimate — [Section Name]**
>
> | Task | Hours | Notes |
> |---|---|---|
> | [Task 1] | X | [Assumption or note] |
> | [Task 2] | X | |
> | **Section Total** | **X** | |
