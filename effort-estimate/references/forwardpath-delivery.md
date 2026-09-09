# ForwardPath Delivery Defaults

Apply this reference only to ForwardPath custom builds, fixed-price estimates, Engineering Report + Effort Estimate documents, or SOW inputs.

## Estimation contract

| Parameter | Value |
|---|---|
| Rate | **$550/hour (CAD)** |
| Pricing model | **Fixed price** — the estimate becomes the SOW price; ForwardPath absorbs overruns |
| Standard monorepo setup | **10 hours** for auth, database, web app, API, queues, and CI/CD; this is the only standard component baseline |
| Developers | **1 developer** unless the project specifies otherwise |
| Developer capacity | **2.5 hours/day** because a developer normally splits time across client projects |
| Contingency | **None** — use point estimates and price levers, not a buffer percentage |
| Cloud | **Azure with Azure Foundry AI resources** unless the client specifies otherwise |
| Authentication when undiscussed | TBD |
| Recording link when unavailable | TBD |

AI-assisted engineering is assumed. Estimate aggressively but realistically for enterprise-grade scale and maintainability. A non-Bun/TypeScript/Next.js application may require setup beyond the standard monorepo baseline.

## Included developer hours

- Design and mockup passes before implementation
- Deployment and DevOps beyond the standard setup, including production and client-environment infrastructure
- Developer self-testing
- UAT bug-fix cycles

## Excluded developer hours

- Client meetings and project-management overhead
- Data migration, user documentation, and training
- Internal QA reviewer time

## Internal QA

Before customer UAT, ForwardPath QA reviews the application, provides feedback, and developers resolve issues.

| App complexity | QA phase added to calendar time |
|---|---|
| Simple: 1–2 core flows, no integrations | 2–3 days |
| Medium: several flows, 1–2 integrations | 1 week |
| Complex: many flows, 3+ integrations, or AI pipelines | 2 weeks |

Estimate developer QA-fix hours as a separate line based on project complexity and risk. Do not bill QA reviewer time.

## Timeline calculation

```text
Build weeks = total developer hours / 2.5 hours per day / 5 days per week
Estimated timeline = build weeks + internal QA phase + minimum 3 weeks of client-led UAT
```

Convert a QA phase expressed in days to weeks by dividing by five.
