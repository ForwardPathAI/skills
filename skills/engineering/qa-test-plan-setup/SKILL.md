---
name: qa-test-plan-setup
description: One-time creation of the Notion QA Test Plan database with the fixed Forward Path schema.
disable-model-invocation: true
---

# QA Test Plan Setup

Create a project's **QA Test Plan** Notion database — the canonical store the `qa-test-plan` skill appends to and QA works through during regression runs. **One database per project**; run this once per project.

## Steps

### Step 1: Pick the project and parent

Ask the user which project this plan is for and where the database should live (a Notion parent page). Title the database exactly `<Project> — QA Test Plan` — the `qa-test-plan` skill finds it by searching this pattern.

Done when: project name and parent page confirmed by the user.

### Step 2: Create the database

`notion-create-database` under the parent with this schema:

| Property | Type | Options / notes |
|---|---|---|
| Test Case | Title | Short imperative name, e.g. "Login rejects expired password" |
| Feature | Select | One option per feature area; grows as features ship |
| Steps | Rich text | Numbered tester steps |
| Expected Result | Rich text | What a pass looks like |
| Category | Multi-select | `UI`, `API`, `Edge Case`, `Integration`, `Performance` |
| Priority | Select | `Critical`, `High`, `Medium`, `Low` |
| Status | Select | `Not Started`, `Pass`, `Fail`, `Blocked` |
| Last Updated | Last edited time | Automatic |

This schema is the single source of truth at creation; afterwards the live database is — `qa-test-plan` reads options from Notion at runtime, so QA may add Feature/Category options directly in Notion without touching either skill.

Done when: database exists with all eight properties, verified by fetching it back.

### Step 3: Seed one example row

Add a single reference row so QA sees the intended shape:

- Test Case: `Example — user can log in`
- Feature: `Auth`
- Steps: `1. Open the app. 2. Enter valid credentials. 3. Submit.`
- Expected Result: `User lands on the home screen, session persists on refresh.`
- Category: `UI`
- Priority: `Critical`
- Status: `Not Started`

Done when: row visible in the database.

### Step 4: Record the database URL

Report the database URL. If run from the app repo (or the user points to it), save the URL there as `qa/qa-config.yml`:

```yaml
notion_database: <url>
```

`qa-test-plan` reads this first when locating the database, skipping search entirely.

Done when: URL reported, and saved to the app repo when one is available.

## Related

- `qa-test-plan` — generates and appends test cases; run it after every feature release.
