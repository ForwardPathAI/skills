---
name: cloud-agent-pr-stats
description: Count and summarize pull requests opened by cloud coding agents (Cursor, Codex, Devin, Claude, Copilot) across every repo in a GitHub organization for a given date range, identified by branch-name prefix. Use when the user asks how many PRs were opened by cloud agents, bots, or specific tools like Cursor — phrases like "how many cursor PRs last week", "what % of PRs are from agents", "cloud-agent PR report", "agent-authored PRs by repo".
---

# Cloud Agent PR Stats

Report how many pull requests were opened by cloud coding agents across a GitHub org over a date window, broken down by repo, with a totals line and the agent share of overall PR volume.

Cloud agents are identified by **branch-name prefix**, not author — agents commonly push as a human user but use a sentinel prefix (`cursor/`, `codex/`, `devin/`, `claude/`, `copilot/`).

## Prerequisites

- `gh` authenticated with access to the target org (`gh auth status`).
- `jq` available on PATH.
- The org name. Default to **ForwardPathAI** when the user doesn't name one and the work is internal.

Stop and tell the user what is missing if any prerequisite fails.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Resolve org, date window, and agent prefixes
- [ ] Step 2: List non-archived repos in the org
- [ ] Step 3: Fetch PRs per repo in parallel
- [ ] Step 4: Verify no repo's PR history was truncated inside the window
- [ ] Step 5: Aggregate and report
```

### Step 1: Resolve inputs

| Input | Default | Notes |
|-------|---------|-------|
| **Org** | `ForwardPathAI` | Confirm if ambiguous. |
| **Window** | Last 7 calendar days, ending yesterday | Convert relative phrases ("last week", "this month") to absolute ISO dates against today. Use `[start, end)` — end is exclusive. |
| **Agent prefixes** | `cursor/`, `codex/`, `devin/`, `claude/`, `copilot/` | Add or restrict per user. The user-specified set wins. |
| **PR state** | `all` | Includes open, merged, and closed PRs opened in the window. |

State the resolved values back to the user in one line before running anything heavy.

### Step 2: List repos

```bash
gh repo list <ORG> --limit 500 --json name,isArchived \
  | jq -r '.[] | select(.isArchived==false) | .name'
```

Archived repos are skipped by default — agents don't open PRs there. Include them only if the user asks.

### Step 3: Fetch PRs per repo (parallel)

`gh search prs` is capped at 1000 results and doesn't return `headRefName`, so it can't be used directly. Run `gh pr list` per repo in parallel and write JSON to a scratch dir:

```bash
SCRATCH=$(mktemp -d)
for repo in $REPOS; do
  gh pr list --repo <ORG>/$repo --state all --limit 500 \
    --json number,title,headRefName,createdAt,author,url \
    > "$SCRATCH/${repo}.json" 2>/dev/null &
done
wait
```

Run in parallel (`&` + `wait`) — 30 repos sequentially is slow, in parallel it's seconds.

### Step 4: Verify no truncation inside the window

`gh pr list --limit 500` returns the **most recent** 500 PRs. If a repo has >500 PRs and the oldest fetched PR is **newer than the window start**, the window is incomplete:

```bash
for f in "$SCRATCH"/*.json; do
  n=$(jq 'length' "$f")
  if [ "$n" -ge 500 ]; then
    oldest=$(jq -r '[.[].createdAt] | min' "$f")
    echo "$f hit limit, oldest=$oldest"
  fi
done
```

If `oldest >= window_start`, **re-fetch that repo with `--limit 1000`** (or page via `gh api graphql`). Do not report numbers until this is clean — silent truncation invalidates the count.

### Step 5: Aggregate and report

Filter each repo's PRs to the window, count those whose `headRefName` starts with any agent prefix, and sum:

```bash
START="2026-05-18T00:00:00Z"
END="2026-05-25T00:00:00Z"
PREFIXES='["cursor/","codex/","devin/","claude/","copilot/"]'

jq -s --arg start "$START" --arg end "$END" --argjson prefixes "$PREFIXES" '
  [.[][] | select(.createdAt >= $start and .createdAt < $end)] as $window
  | {
      total: ($window | length),
      agent: ([ $window[] | select(.headRefName as $b | $prefixes | any(. as $p | $b | startswith($p))) ] | length),
      by_repo: ($window | group_by(.url | capture("github.com/[^/]+/(?<r>[^/]+)/").r)
        | map({
            repo: .[0].url | capture("github.com/[^/]+/(?<r>[^/]+)/").r,
            agent: [.[] | select(.headRefName as $b | $prefixes | any(. as $p | $b | startswith($p)))] | length,
            total: length
          })
        | map(select(.agent > 0))
        | sort_by(-.agent))
    }
' "$SCRATCH"/*.json
```

Report format:

```
Cloud agent PRs in <ORG>, <start> to <end-inclusive>:

- Total PRs opened: <N>
- From agent branches: <M>
- Agent share: <M/N as %>

By repo (agent / total), only repos with ≥1 agent PR:
| Repo | Agent | Total |
|------|-------|-------|
| ...  | ...   | ...   |
```

Always quote **end-inclusive** to the user (`May 18–24`), but compute with **end-exclusive** (`< 2026-05-25T00:00:00Z`) to avoid timezone edge cases.

## Decision table

| Situation | Action |
|-----------|--------|
| User says "last week" | Interpret as the prior Mon–Sun unless context says otherwise; confirm if ambiguous. |
| User asks for a single repo | Skip Step 2; jump to Step 3 with that one repo. |
| User asks for a single agent (e.g. "cursor") | Restrict prefixes to that one. |
| Repo has >500 PRs and oldest fetched is inside the window | Re-fetch with higher `--limit`, or use `gh api graphql` pagination. |
| Org has bots that match a prefix coincidentally | Spot-check 1–2 PR URLs to confirm; mention the caveat in the report. |
| User wants closed-only or merged-only | Filter on `state` after fetch. |

## Anti-patterns

- Using `gh search prs` — it doesn't return `headRefName`, so you can't identify agent branches.
- Filtering by `author.login` — agents push as their human operator; branch prefix is the signal.
- Reporting numbers without checking Step 4 truncation — a repo that hit `--limit 500` silently undercount.
- Hardcoding today's date inside the skill — always derive the window from the user's request and current date.
- Skipping archived repos when the user asked for a historical window that includes time before archival.

## Examples

**Default org, last week:**

> Cloud agent PRs in ForwardPathAI, 2026-05-18 to 2026-05-24:
> - Total PRs opened: 199
> - From agent branches: 44
> - Agent share: 22.1%

**Single agent, single repo:**

> `cursor/*` PRs in ForwardPathAI/ButtconRAG, 2026-05-18 to 2026-05-24: 23 of 45 (51%).
