#!/usr/bin/env bash
#
# security-sweep scan — READ-ONLY. Changes nothing, opens nothing.
#
# Enumerates open Dependabot alerts across every active repo in a GitHub org,
# drops alerts an open PR already covers, collapses duplicate alerts for the
# same package, and groups the rest into fix batches (one per repo per
# ecosystem). Writes a plan JSON and prints a one-screen summary.
#
# Usage: ./scan.sh [ORG] [OUT_JSON]
#   ORG       GitHub org                 (default: ForwardPathAI)
#   OUT_JSON  plan output path           (default: ./sweep-plan.json)
#
# Env:
#   REPOS       space-separated repo subset; skips org enumeration
#   REPO_LIMIT  max repos to enumerate    (default: 500)
#   MAX_JOBS    parallel API fetchers     (default: 8)
#
set -euo pipefail

case "${1:-}" in
  -h|--help) awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; exit 0 ;;
esac

ORG="${1:-ForwardPathAI}"
OUT="${2:-./sweep-plan.json}"
REPO_LIMIT="${REPO_LIMIT:-500}"
MAX_JOBS="${MAX_JOBS:-8}"

for bin in gh jq; do
  command -v "$bin" >/dev/null || { echo "security-sweep: $bin not on PATH" >&2; exit 1; }
done
gh auth status >/dev/null 2>&1 || { echo "security-sweep: gh not authenticated" >&2; exit 1; }

SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
: > "$SCRATCH/unreadable.txt"

# ---------------------------------------------------------------- repos -----
# Active = not archived, not a fork, not empty, has a default branch.
if [ -n "${REPOS:-}" ]; then
  printf '%s\n' ${REPOS} > "$SCRATCH/repos.txt"
else
  gh repo list "$ORG" --limit "$REPO_LIMIT" --no-archived --source \
      --json name,isEmpty,isFork,defaultBranchRef \
    | jq -r '.[]
        | select(.isEmpty == false and .isFork == false and .defaultBranchRef != null)
        | .name' \
    | sort > "$SCRATCH/repos.txt"
fi
REPO_COUNT=$(wc -l < "$SCRATCH/repos.txt" | tr -d ' ')
[ "$REPO_COUNT" -gt 0 ] || { echo "security-sweep: no active repos found in $ORG" >&2; exit 1; }

# ------------------------------------------------------- alerts + open PRs ---
fetch_repo() {
  repo="$1"
  if ! gh api --paginate \
        "/repos/$ORG/$repo/dependabot/alerts?state=open&per_page=100" \
        > "$SCRATCH/alerts-$repo.json" 2> "$SCRATCH/alerts-err-$repo.txt"; then
    printf '%s\n' "$repo" >> "$SCRATCH/unreadable.txt"
    printf '[]\n' > "$SCRATCH/alerts-$repo.json"
  fi
  if ! gh pr list --repo "$ORG/$repo" --state open --limit 200 \
        --json number,title,headRefName,url > "$SCRATCH/prs-$repo.json" 2>/dev/null; then
    printf '[]\n' > "$SCRATCH/prs-$repo.json"
  fi
}
export -f fetch_repo
export ORG SCRATCH

xargs -P "$MAX_JOBS" -I{} bash -c 'fetch_repo "$1"' _ {} < "$SCRATCH/repos.txt"

UNREADABLE=$(wc -l < "$SCRATCH/unreadable.txt" | tr -d ' ')
if [ "$UNREADABLE" -eq "$REPO_COUNT" ]; then
  echo "security-sweep: every repo returned an error for /dependabot/alerts." >&2
  echo "  Likely a missing token scope. Fix: gh auth refresh -h github.com -s security_events" >&2
  echo "  First error was:" >&2
  cat "$SCRATCH"/alerts-err-* 2>/dev/null | head -3 >&2
  exit 1
fi

# ------------------------------------------------------------ plan per repo --
cat > "$SCRATCH/plan.jq" <<'JQ'
def semver: [splits("[^0-9]+")] | map(select(length > 0) | tonumber);
def norm:   ascii_downcase | gsub("[^a-z0-9]+"; "-");
def sevrank: {"critical": 4, "high": 3, "medium": 2, "moderate": 2, "low": 1}[.] // 0;
# Dependabot's branch/group slug per alert ecosystem.
def ecoslug: {"npm": "npm_and_yarn", "pip": "pip", "go": "go_modules", "nuget": "nuget",
              "rust": "cargo", "actions": "github_actions", "rubygems": "bundler",
              "composer": "composer", "maven": "maven", "gradle": "gradle",
              "pub": "pub", "swift": "swift"}[.] // .;

{ repo: $repo, alerts: ($alerts[0] // []), prs: ($prs[0] // []) }
| .repo as $repo

# Open PRs, annotated with the package name Dependabot puts in its title.
| ( [ .prs[]
      | . + { bumped: ( [ (.title // "" | ascii_downcase | match("bump +([^ ]+) +from").captures[0].string) ] | first ) } ]
  ) as $prs

# Grouped Dependabot PRs ("Bump the npm_and_yarn group with 3 updates") name no
# package, so coverage can't be decided from metadata — the agent reads the diff.
# Keyed by Dependabot's ecosystem slug so an npm group PR isn't flagged on a pip batch.
| ( [ $prs[]
      | select((.title // "") | ascii_downcase | test("bump the .* group"))
      | { number, slug: ( [ (.headRefName | ascii_downcase | match("^dependabot/([^/]+)/").captures[0].string) ] | first ) } ]
  ) as $grouped

| ( [ .alerts[]
      | select(.state == "open")
      | { number,
          ghsa:             .security_advisory.ghsa_id,
          severity:         (.security_advisory.severity // "unknown"),
          ecosystem:        (.dependency.package.ecosystem // "unknown"),
          package:          (.dependency.package.name // "unknown"),
          manifest:         (.dependency.manifest_path // ""),
          scope:            (.dependency.scope // "unknown"),
          vulnerable_range: (.security_vulnerability.vulnerable_version_range // ""),
          patched:          (.security_vulnerability.first_patched_version.identifier // null),
          url:              .html_url } ]
  ) as $alerts

# An open PR covers an alert when its title bumps that exact package, or its
# branch is dependabot/<eco>/[path/]<pkg>-<version>. The trailing "-[0-9]" stops
# `next` matching a `next-auth` branch.
| ( [ $alerts[]
      | . as $a
      | ( [ $prs[]
            | select( (.bumped == ($a.package | ascii_downcase))
                      or ((.headRefName | norm) | test("-" + ($a.package | norm) + "-[0-9]")) ) ]
          | first ) as $pr
      | $a + { covering_pr: (if $pr then {number: $pr.number, url: $pr.url, branch: $pr.headRefName} else null end) } ]
  ) as $alerts

| ( [ $alerts[] | select(.covering_pr != null)
      | {repo: $repo, package, ecosystem, severity, alert: .number, pr: .covering_pr.number, url: .covering_pr.url} ] ) as $covered
| ( [ $alerts[] | select(.covering_pr == null and .patched == null)
      | {repo: $repo, package, ecosystem, severity, alert: .number, url, vulnerable_range} ] )   as $no_fix
| ( [ $alerts[] | select(.covering_pr == null and .patched != null) ] )                          as $fixable

# One fix per (ecosystem, package): several advisories on one package collapse to
# the highest patched version — this is what keeps 5 alerts from becoming 5 PRs.
| ( [ $fixable
      | group_by([.ecosystem, .package])[]
      | { ecosystem:  .[0].ecosystem,
          package:    .[0].package,
          target:     ( max_by(.patched | semver) | .patched ),
          severity:   ( max_by(.severity | sevrank) | .severity ),
          scope:      ( [ .[].scope ] | unique | join("+") ),
          manifests:  ( [ .[].manifest ] | map(select(. != "")) | unique ),
          alerts:     [ .[] | {number, ghsa, severity, vulnerable_range, patched, url} ] } ] ) as $fixes

| { repo: $repo,
    alert_count: ($alerts | length),
    batches: [ $fixes
      | group_by(.ecosystem)[]
      | . as $g
      | ($g[0].ecosystem) as $eco
      | { repo: $repo,
          ecosystem: $eco,
          max_severity: ( [ $g[].severity ] | max_by(sevrank) ),
          max_severity_rank: ( [ $g[].severity | sevrank ] | max ),
          manifests: ( [ $g[].manifests[] ] | unique ),
          existing_sweep_pr: ( [ $prs[]
              | select((.headRefName | norm) | startswith("security-sweep-" + ($eco | norm)))
              | {number, branch: .headRefName, url} ] | first ),
          verify_against_prs: ( [ $grouped[]
              | select(.slug == null or .slug == ($eco | ecoslug))
              | .number ] ),
          fixes: ( $g | sort_by(- (.severity | sevrank)) ) } ],
    covered: $covered,
    no_fix: $no_fix }
JQ

: > "$SCRATCH/plans.jsonl"
while read -r repo; do
  jq -n --arg repo "$repo" \
     --slurpfile alerts "$SCRATCH/alerts-$repo.json" \
     --slurpfile prs "$SCRATCH/prs-$repo.json" \
     -f "$SCRATCH/plan.jq" >> "$SCRATCH/plans.jsonl"
done < "$SCRATCH/repos.txt"

UNREADABLE_JSON=$(jq -R . < "$SCRATCH/unreadable.txt" | jq -s 'sort')

jq -s --arg org "$ORG" --argjson unreadable "$UNREADABLE_JSON" '
  {
    org: $org,
    repos_scanned: (length),
    repos_unreadable: $unreadable,
    repos_clean: [ .[] | select(.alert_count == 0) | .repo ],
    batches: ( [ .[].batches[] ] | sort_by(-.max_severity_rank, .repo) ),
    covered: ( [ .[].covered[] ] | sort_by(.repo) ),
    no_fix:  ( [ .[].no_fix[]  ] | sort_by(.repo) )
  }
' "$SCRATCH/plans.jsonl" > "$OUT"

# ---------------------------------------------------------------- summary ----
jq -r '
  "security-sweep plan for \(.org)",
  "  repos scanned:       \(.repos_scanned)",
  "  repos clean:         \(.repos_clean | length)",
  "  repos unreadable:    \(.repos_unreadable | length)\(if (.repos_unreadable|length) > 0 then "  (" + (.repos_unreadable|join(", ")) + ")" else "" end)",
  "  batches to fix:      \(.batches | length)   packages: \([.batches[].fixes[]] | length)   alerts: \([.batches[].fixes[].alerts[]] | length)",
  "  already covered:     \(.covered | length)",
  "  no fix available:    \(.no_fix | length)",
  "",
  ( .batches[] | "  \(.repo)  [\(.ecosystem)]  \(.max_severity)  \(.fixes | length) pkg\(if .existing_sweep_pr then "  → existing sweep PR #\(.existing_sweep_pr.number)" else "" end)\(if (.verify_against_prs|length) > 0 then "  ⚠ grouped PRs \(.verify_against_prs)" else "" end)" )
' "$OUT"

echo
echo "plan written to $OUT"
