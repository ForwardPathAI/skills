---
name: qa-test-plan
description: Generate and maintain customer-shareable QA test plans for Forward Path apps. Use when asked to create a QA/UAT/acceptance test plan (generate), sync a plan after feature changes (update), report test coverage gaps or drift (audit), or publish a plan to Notion for customer QA (publish). Also reached by automation that keeps test plans in line as the app evolves.
---

# QA Test Plan

Produce and maintain a **customer-shareable QA test plan** for a Forward Path custom app build. The canonical plan is markdown at `qa/test-plan.md` — version-controlled, diffable, agent-maintainable; `publish` mirrors it to Notion for customer collaboration.

Everything keys off the **surface**: the set of routes, backend endpoint groups, and feature flags a tester can exercise. Forward Path apps share a skeleton (`ForwardPath.Server` + `ForwardPath.Web`), so the surface is enumerable from code — which is what makes coverage and **drift** mechanical to check.

## Modes

Pick the mode from the request. If ambiguous, ask.

| Mode | Use when | Effect |
|------|----------|--------|
| **generate** | No `qa/test-plan.md` yet, or "create a test plan for this app" | Bootstrap a full plan from the code surface. Writes `qa/test-plan.md` (+ `qa/qa-config.yml` if missing). |
| **update** | After a feature change, "sync the test plan" | Diff live surface vs. plan; add cases for new surface, flag stale cases, bump `last_synced_commit`. Edits in place. |
| **audit** | "check coverage / drift"; called by automation | **Read-only.** Emit a gap report (uncovered surface + orphaned cases). No edits. This is the engine for CI / scheduled-agent / Cursor automation. |
| **publish** | "publish to Notion for the customer" | Render `qa/test-plan.md` to Notion (per customer). Idempotent: update the existing page if present. |

## Prerequisites

- Run from the **app repo root** (the one with `src/ForwardPath.Server` / `src/ForwardPath.Web`), not the skills repo.
- `qa/qa-config.yml` — read it if present; if absent, auto-detect the skeleton paths (see [Surface enumeration](#surface-enumeration)) and write a config in `generate`.
- For `publish`: Notion MCP available and `publish.notion_parent` set in config. Stop and ask for the parent page/DB id if missing.

## Surface enumeration (shared by generate / update / audit)

Build the **live surface** = the set of things a tester can exercise. Resolve paths from `qa/qa-config.yml` `surfaces:`; defaults match the FP skeleton.

1. **Routes** — parse the Vue router (default `src/ForwardPath.Web/src/router/index.js`). Collect each `path:` (resolve nested `children` to full paths, e.g. `/proposals` + `list` → `/proposals/list`) and its `meta` (`requiresAuth`, `requiresAdmin`, `requiresSuperAdmin`). Skip pure redirects and the catch-all.
2. **Backend endpoint groups** — list modules in `src/ForwardPath.Server/app/api/v1/endpoints/` (ignore `__init__`, `__pycache__`, non-`.py`). For accurate prefixes, read the router-include file (`app/api/v1/api.py` or `router.py`) for `prefix="/api/v1/..."`; fall back to `/api/v1/<module>` when unresolved.
3. **Feature flags** — keys in `FEATURE_FLAG_REGISTRY` (default `app/core/feature_flags_registry.py`) **plus** `enable_*` connector fields on `Settings` (`app/core/config.py`). Note each flag's default and category.

A surface item is identified by a stable token used in `Covers:` tags:
- Route: the path, e.g. `/chat`, `/proposals/list`
- Endpoint: `/api/v1/<group>`, e.g. `/api/v1/search`
- Flag: `flag:<key>`, e.g. `flag:enable_hybrid_search`

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Determine mode + load/auto-detect qa/qa-config.yml
- [ ] Step 2: Enumerate the live surface (routes, endpoints, flags)
- [ ] Step 3: Run the mode (generate / update / audit / publish)
- [ ] Step 4: Self-check against "Before finishing"
```

### generate

1. Enumerate the surface.
2. Read `templates/test-plan-template.md`. Fill the document header (overview, scope, in/out of scope, approach & roles, environments, entry/exit/pass-fail criteria) from `qa-config.yml` + the README.
3. Group surface into **suites** by feature area (one `TS-<AREA>`). Map routes/endpoints/flags into the suite they belong to.
4. For each suite, write **test cases** using `templates/test-case-template.md`:
   - Full detail (steps + expected) for **Critical/High** flows — auth, the primary chat→generate→export paths, role gating, connector ingest.
   - Stubs (title, priority, `Covers:`, "_steps TBD_") for Medium/Low — enough to show structure without faking exhaustive coverage. **Log** how many are stubs so the team knows what's left.
5. Build the **Coverage map** table: every surface token → covering `TC-` IDs. This is the drift index.
6. Set frontmatter `last_synced_commit` to current `git rev-parse --short HEAD`.
7. Write `qa/test-plan.md`. If `qa/qa-config.yml` didn't exist, write one from `templates/qa-config.example.yml` with detected paths filled in.

### update

1. Enumerate the surface. Collect all `Covers:` tokens from the existing plan.
2. Compute the set difference (see [Drift detection](#drift-detection)).
3. For **uncovered** tokens: add cases (or stubs) to the right suite; create the suite if the feature area is new.
4. For **orphaned** tokens (in plan, not in code): do **not** delete — mark the case `> ⚠️ STALE: covers \`<token>\` no longer in code (commit <sha>). Review.` so a human decides.
5. Update the Coverage map and bump `last_synced_commit`. Preserve existing case IDs, `Status:`, and customer edits — only append/annotate.

### audit (read-only — no edits)

1. Enumerate the surface. Collect `Covers:` tokens from the plan.
2. Compute drift. Emit a markdown report only:

```markdown
## QA test-plan drift report — <app> @ <sha>
**Uncovered (N):** new surface with no test case
- `/api/v1/reports` (endpoint)
- `flag:enable_sql_context`

**Orphaned (M):** cases covering surface not found in code
- TC-PROP-007 covers `/proposals/archive`

**Coverage:** X/Y surface items covered (Z%).
```

3. If clean, say so explicitly ("0 uncovered, 0 orphaned"). This output is designed to drop into a PR comment or Linear issue.

### publish

1. Read `qa/test-plan.md` and `publish.notion_parent` from config.
2. `notion-search` for an existing page titled `<app> — QA Test Plan` under the parent.
   - Found → `notion-update-page` to replace its body with the rendered plan.
   - Not found → `notion-create-pages` under `notion_parent`.
3. Render markdown to Notion blocks: H2 per suite, each case as a toggle/section with its steps and expected. Keep `Status:` checkboxes so customers can tick them in Notion.
4. Return the Notion URL. Note in the plan footer: "Published to Notion: <url> (<sha>)".

## Drift detection

```
live      = routes ∪ endpoints ∪ flags        (from code)
covered   = all Covers: tokens                 (from plan)
uncovered = live − covered                      → need cases
orphaned  = covered − live                      → flag stale (never auto-delete)
```

Normalize tokens before comparing (lowercase, strip trailing slashes, `flag:` prefix for flags). Treat `:id`/`:pathMatch` params as part of the base path.

## Test plan format

`templates/test-plan-template.md` and `templates/test-case-template.md` are the structure — fill them, don't reinvent the layout. The rules that govern them:

- **Stable IDs** — suites `TS-<AREA>`, cases `TC-<AREA>-<NNN>`. Never renumber an existing case; only append. Areas: `AUTH, CHAT, PROP, RES, PROF, MEM, ADMIN, CONN, DOC, KG` — add new ones to `qa-config.yml`.
- **`Covers:` is the traceability contract** — each case lists the exact surface tokens it exercises (`/route`, `/api/v1/<group>`, `flag:<key>`). An omitted or invented token breaks drift detection.
- **Coverage map** — the table mapping every surface token to its covering case(s); keep it in sync with the cases. It is the drift index.

## Before finishing

- [ ] Every `Covers:` token resolves to a real route/endpoint/flag in the current code.
- [ ] Coverage map matches the cases (no token listed without a `TC-` behind it).
- [ ] Existing case IDs, `Status:` values, and customer edits preserved (update mode).
- [ ] `last_synced_commit` bumped to current HEAD.
- [ ] Reads professionally for a customer — no internal jargon, secrets, or file paths leaking into the customer-facing prose (file paths belong only in `Covers:`/coverage map).
- [ ] Stub count reported so the team knows what still needs fleshing out.

## Anti-patterns

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| Inventing routes/endpoints/flags | Plan diverges from reality | Only tag surface that exists in code |
| `Covers:` "everything" or omitted | Breaks drift detection | One precise token list per case |
| Deleting orphaned cases automatically | Destroys customer QA history / may be a rename | Mark STALE; let a human decide |
| Renumbering case IDs | Breaks external references & Notion links | Append new IDs only |
| Faking exhaustive coverage | False confidence | Stub Medium/Low cases; report the stub count |
| Leaking secrets/internal paths into customer prose | Not customer-shareable | Keep paths in `Covers:` only |
| Editing in `audit` mode | Audit must be safe for automation | Audit is read-only; use `update` to change |
| Hardcoding ButtconRAG specifics | Skill must generalize | Drive everything from `qa-config.yml` + enumeration |

## Related

- When a coverage gap should become tracked work, file it with the `issue-writer` skill and link the issue in the case's `Linear:` field.
