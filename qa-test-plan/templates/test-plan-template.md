---
app: <AppName>
customer: <Customer Name>
version: 0.1.0
last_synced_commit: <short-sha>
owners: [qa@forwardpath.ai]
environments: [local, dev, prod]
---

# <AppName> — QA Test Plan

> Customer-facing QA test plan. Source of truth lives in the repo at `qa/test-plan.md`; this document is published to Notion for collaborative QA. Tick the **Status** boxes as you run each case and leave comments inline.

## 1. Overview & scope

<1–2 paragraphs: what the app does and what this plan validates.>

## 2. Features to be tested

- <feature area> — <one line>

### Not to be tested (this cycle)

- <explicitly excluded area> — <why>

## 3. Test approach & roles

| Aspect | Detail |
|--------|--------|
| Manual vs. automated | <e.g. Manual UAT now; automation tracked separately> |
| Who runs what | <Customer QA runs X; Forward Path runs Y> |
| Defect handling | <where bugs are filed, severity scale> |
| Sign-off | <who approves exit> |

## 4. Environments & test data

| Environment | URL | Notes |
|-------------|-----|-------|
| local | https://<app>.localhost | dev only |
| dev | <url> | shared test data |
| prod | <url> | release validation |

- **Auth:** SSO via Azure AD. Test accounts per role: user / admin / super-admin.
- **Test data / prerequisites:** <seeded docs, connector sync completed, etc.>

## 5. Criteria

- **Entry:** <when QA may begin — e.g. deploy green, connectors synced, accounts provisioned.>
- **Exit:** <when QA is done — e.g. all Critical/High pass, no open Sev-1/2.>
- **Pass/Fail:** a case passes only if every Expected result holds; otherwise fail and file a defect.

## 6. Coverage map

Every testable surface item → the test case(s) that cover it. Used to detect drift as the app evolves.

| Surface | Type | Covered by |
|---------|------|------------|
| `/chat` | route | TC-CHAT-001 |
| `/api/v1/search` | endpoint | TC-CHAT-001 |
| `flag:enable_hybrid_search` | flag | TC-CHAT-001 |

## 7. Test suites

<!-- One TS-<AREA> per feature area; cases use the test-case template. -->

### TS-<AREA> — <Suite name>

<cases here>
