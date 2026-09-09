# ForwardPath Delivery Defaults

Apply this reference only to ForwardPath custom builds, fixed-price estimates, Engineering Report + Effort Estimate documents, or SOW inputs.

These values are defaults only. Preserve user-confirmed project inputs and approved price-lever assumptions; use the table below only where the effective estimation contract remains unspecified.

## Estimation contract

| Parameter | Value |
|---|---|
| Rate | **$550/hour (CAD)** |
| Pricing model | **Fixed price** — the estimate becomes the SOW price; ForwardPath absorbs overruns |
| Standard monorepo setup | **10 hours** for auth, database, web app, API, queues, and CI/CD; this is the only standard component baseline |
| Developers | **1 developer** unless the project specifies otherwise |
| Developer capacity | **2.5 hours/day per developer** because developers normally split time across client projects |
| Contingency | **None** — use point estimates and price levers, not a buffer percentage |
| Cloud | **Azure with Azure Foundry AI resources** unless the client specifies otherwise |
| Authentication when undiscussed | TBD |
| Recording link when unavailable | TBD |

AI-assisted engineering is assumed. Estimate aggressively but realistically for enterprise-grade scale and maintainability. A non-Bun/TypeScript/Next.js application may require setup beyond the standard monorepo baseline.

## Included developer hours

- Design and mockup passes before implementation
- Deployment and DevOps beyond the standard setup, including production and client-environment infrastructure
- Developer self-testing
- UAT bug-fix cycles, tracked separately from pre-QA build hours for timeline calculation

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

Count the standard monorepo setup once per full-build estimate. Keep it out of technical-section totals and add it as one standalone rollup line.

## Timeline calculation

```text
Pre-QA build hours = total developer hours - internal QA-fix hours - UAT bug-fix hours
Build weeks = pre-QA build hours / (effective developers * effective hours per developer per day * 5 days per week)
Estimated timeline = build weeks + internal QA phase + minimum 3 weeks of client-led UAT
```

Use the confirmed Developers and capacity values when provided; otherwise use the defaults above. The formula assumes the pre-QA work divides evenly across the effective developers. If dependencies limit parallelism, use a lower effective developer count and state it.

QA-fix and UAT bug-fix hours remain in the billed total but are excluded from pre-QA build hours because they occur inside the QA and UAT phases. Keep both fix-hour amounts identifiable in the estimate or its calculation notes. If the planned fixes cannot fit inside a phase at the effective team capacity, extend that phase and state the adjustment. Convert a QA phase expressed in days to weeks by dividing by five.
