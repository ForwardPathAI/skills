# Breaking-Change Scan

Run during Step 2 for `${LAST_TAG}..origin/$DEFAULT_BRANCH`. Check only paths that **exist in the repo**; record **no findings** explicitly when clean.

Focus on changes that break **customer or downstream deployments** — not application-internal schema migrations that run automatically at startup unless the repo documents manual migration steps.

## Discover paths first

Before scanning, locate env and infra surfaces in the repo:

```bash
# Common env documentation (use whichever exist)
ls -la .env.example .env.sample .env.template env.example 2>/dev/null

# Common infra / deploy directories
ls -d infra/ infrastructure/ terraform/ deploy/ ops/ .github/workflows/ 2>/dev/null

# Docker / compose (any location)
find . -maxdepth 4 -name 'Dockerfile' -o -name 'docker-compose*.yml' -o -name 'compose*.yml' 2>/dev/null | head -20
```

## Path scans

```bash
LAST_TAG="<from Step 1>"
DEFAULT_BRANCH="<from Step 1>"
RANGE="${LAST_TAG}..origin/$DEFAULT_BRANCH"
```

Run `git diff "$RANGE" --stat -- <path>` for each discovered path. Skip missing paths.

### Environment and configuration

Any env example or documented config file found above, plus:

- `README*` sections that list required environment variables
- Config templates (`config.example.*`, `*.env.dist`, Helm `values*.yaml` with env blocks)

Summarize: **added, removed, or renamed** variables; new **required** values; changed documented semantics.

### Infrastructure and deployment

Changes under discovered infra/deploy directories and release-related workflows:

```bash
git diff "$RANGE" --name-only -- .github/workflows/
```

Flag workflow files whose diff touches deploy, terraform, helm, kubernetes, or container publish steps.

Summarize: new cloud resources, changed secret names, networking, IAM, or deploy mechanics that a customer must replicate manually.

### Container build (when present)

Diff any changed `Dockerfile` or compose file. Summarize: base image, exposed ports, entrypoint/CMD, or required build args that affect how the image is run — not routine dependency bumps.

### Explicit breaking signals in commits

```bash
git log "$RANGE" --pretty=format:"%h %s" | grep -iE 'BREAKING|breaking change|feat!:|fix!:|!:' || true
```

Flag any match with the commit hash and subject.

## Out of scope (do not flag by default)

- ORM/database migration files when the repo runs migrations automatically on deploy/startup and docs do not require manual steps
- Internal test-only or dev-only config with no documented customer surface
- Application code changes with no env, infra, or deploy doc impact

If the repo's README or deploy docs **explicitly** require manual migrations or DBA steps, treat migration/doc changes in those paths as findings.

## Deployment impact categories

| Category | Examples |
|----------|----------|
| **Env vars** | New required var, renamed var, removed var, changed semantics in env example or deploy docs |
| **Infra** | Terraform/Bicep/Helm changes, new secrets, networking, IAM |
| **Build/deploy** | Dockerfile or release workflow changes affecting how artifacts are built, tagged, or published |
| **Auth / integrations** | New OAuth redirect URIs, API scopes, webhook endpoints documented for operators |
| **Explicit breaking** | Commit subject/body marks breaking change |

## Semver (production)

Follow the repo's tag convention (infer prefix from `LAST_TAG`).

| Bump | When |
|------|------|
| **patch** (default) | Fixes, chores, deps, backwards-compatible features |
| **minor** | User explicitly requests a feature release bump |
| **major** | User explicitly requests major, or confirms deployment-breaking changes warrant it |

At `0.y.z`, semver treats minor as potentially breaking; still default **patch** unless the user directs otherwise.

## Deployment handoff flag

When any finding has deployment impact, Step 2 must note:

> Deployment or customer documentation may need updating before operators can deploy this version.

Do not auto-run other skills; flag only.
