# Ecosystem Recipes

Per-ecosystem commands for [security-sweep](SKILL.md) Steps 3–4. Read only the sections whose ecosystems appear in the plan.

Every section answers the same four questions:

- **Detect** — which package manager the repo actually uses.
- **Bump** — the package is declared in a manifest (`fixes[].manifests` is non-empty).
- **Transitive** — the package is in no manifest; something else pulls it in.
- **Verify** — the query that proves the *resolved* version is at or above `target`.

Two rules hold everywhere:

1. Never hand-edit a lockfile. If the tool can't write it, the batch is needs-human.
2. An override/resolution pin is the last rung, not the first. Bump the parent that pulls the vulnerable version when you can — a pin outlives the vulnerability and silently freezes a transitive dep.

## npm (ecosystem `npm`)

**Detect** by lockfile at the repo root: `bun.lock`/`bun.lockb` → bun, `pnpm-lock.yaml` → pnpm, `yarn.lock` → yarn, `package-lock.json` → npm. Two lockfiles present: the one git tracks wins.

**Bump** — run in the workspace directory that declares the package, or target it by filter:

```bash
bun add <pkg>@<target>                              # bun (per workspace dir)
pnpm --filter <workspace> up <pkg>@<target>         # pnpm, one workspace
pnpm up -r <pkg>@<target>                           # pnpm, every workspace declaring it
yarn up <pkg>@<target>                              # yarn berry
yarn upgrade <pkg>@<target>                         # yarn classic
npm install <pkg>@<target> -w <workspace>           # npm workspaces
```

Preserve the range operator the manifest already uses (`^`, `~`, exact). A repo pinning exact versions did it on purpose.

**Transitive** — bump the lockfile first:

```bash
pnpm up -r --depth Infinity <pkg>
npm update <pkg> --depth 99
bun update <pkg>
```

If the resolution is still vulnerable, pin in the **root** `package.json`:

```json
{ "pnpm": { "overrides": { "<pkg>": ">=<target>" } } }   // pnpm
{ "overrides": { "<pkg>": ">=<target>" } }               // npm, bun
{ "resolutions": { "<pkg>": ">=<target>" } }             // yarn
```

**Install + verify**:

```bash
pnpm install && pnpm why <pkg> -r          # every path's resolved version
npm install  && npm ls <pkg> --all
bun install  && bun pm ls --all | grep <pkg>
yarn install && yarn why <pkg>
```

`pnpm why` / `npm ls` print *every* resolution — one stale path means the fix is incomplete.

**Checks**: whichever of `typecheck`, `lint`, `build`, `test` exist in `package.json` scripts, via the detected manager.

## pip (ecosystem `pip`)

**Detect**: `uv.lock` → uv, `poetry.lock` → poetry, `requirements*.in` → pip-tools, plain `requirements*.txt` → direct pin edit.

**Bump**:

```bash
uv lock --upgrade-package "<pkg>==<target>"     # uv (then uv sync)
poetry update <pkg>                             # poetry; poetry add "<pkg>@^<target>" to lift the constraint
# pip-tools: edit the pin in requirements.in, then
pip-compile requirements.in
# plain requirements.txt: edit the pin in place
```

**Transitive** — uv and poetry resolve it from the constraint alone; for pip-tools add the pin to `requirements.in` as an explicit constraint. Bare `requirements.txt`: add `<pkg>>=<target>` as its own line.

**Install + verify**:

```bash
uv sync && uv tree --package <pkg>
poetry install && poetry show <pkg>
pip install -r requirements.txt && pip show <pkg> | head -2
```

**Checks**: `pytest` / `ruff check` / `mypy` only if the repo already configures them.

## go (ecosystem `go`)

Dependabot names the **module path**, which is what `go get` wants.

```bash
go get <module>@v<target>
go mod tidy
```

**Transitive** — same command; the module graph accepts a direct upgrade of an indirect dependency (it lands in `go.mod` marked `// indirect`).

**Verify**:

```bash
go list -m all | grep <module>
go build ./... && go test ./...
govulncheck ./...        # only if already installed
```

Commit `go.mod` **and** `go.sum`.

## nuget (ecosystem `nuget`)

```bash
dotnet add <project.csproj> package <pkg> --version <target>
```

Central package management (`Directory.Packages.props` present): edit the `PackageVersion` there instead, not the csproj.

**Transitive** — add an explicit `PackageReference` at `target` to the project that pulls it, or bump the parent package. Note the pin in the PR body; a new direct reference is a design change reviewers should see.

**Verify**:

```bash
dotnet restore
dotnet list package --include-transitive | grep <pkg>
dotnet build --no-restore && dotnet test --no-build
```

Commit `packages.lock.json` when the repo tracks one.

## rust (ecosystem `rust`)

```bash
cargo update -p <pkg> --precise <target>      # lockfile-only, same semver range
```

If `target` falls outside the manifest's range, edit the version in `Cargo.toml` first, then `cargo update -p <pkg>`.

**Transitive** — `cargo update -p <pkg> --precise <target>` handles it directly.

**Verify**:

```bash
cargo tree -i <pkg>          # inverted tree: every consumer's resolved version
cargo build && cargo test
cargo audit                  # only if already installed
```

## actions (ecosystem `actions`)

The "package" is a repo (`actions/checkout`), the "version" a tag.

**Bump** — edit `uses:` in every workflow under `.github/workflows/` (and any composite action). Match the existing pin style:

```yaml
uses: actions/checkout@v5                    # tag pin → new tag
uses: actions/checkout@<sha>  # v5.0.1       # SHA pin → new SHA, comment updated
```

Resolve a tag's SHA:

```bash
gh api /repos/<owner>/<action>/git/ref/tags/<target> -q .object.sha
```

**Transitive** — a vulnerable action used by another action can't be fixed here; bump the outer action, or report needs-human.

**Verify**: `grep -rn "<owner>/<action>@" .github/` shows no old pin left. There is no install step; the checks are whatever the workflows themselves run once the PR opens.

## rubygems (ecosystem `rubygems`)

```bash
bundle update <gem> --conservative      # bumps the gem, leaves its deps alone
```

Outside the `Gemfile` range: edit the constraint, then `bundle update <gem>`.

**Transitive** — the same command works; `--conservative` keeps the blast radius small.

**Verify**: `bundle list | grep <gem>`, then `bundle exec rspec` / `bundle exec rake` if defined.

## composer (ecosystem `composer`)

```bash
composer require "<pkg>:>=<target>" -W        # -W updates dependencies as needed
composer update <pkg> --with-dependencies     # already required, just stale
```

**Transitive** — `composer update <pkg> --with-dependencies`; if the parent pins it, bump the parent.

**Verify**: `composer show <pkg>`, then `composer validate` and the repo's `phpunit` if configured.

## maven / gradle (ecosystems `maven`, `gradle`)

No reliable CLI edit — change the declaration:

- Maven: the `<version>` in `pom.xml`, or the property/`<dependencyManagement>` entry that sets it.
- Gradle: the version in `build.gradle[.kts]`, or the entry in `gradle/libs.versions.toml`.

**Transitive** — Maven: add a `<dependencyManagement>` entry at `target`. Gradle: a constraint (`implementation("<pkg>") { version { require("<target>") } }`) or a `resolutionStrategy.force`.

**Verify**:

```bash
mvn -q dependency:tree -Dincludes=<group>:<artifact> && mvn -q verify
./gradlew dependencyInsight --dependency <pkg> && ./gradlew build
```

## Anything else

For an ecosystem not listed (`pub`, `swift`, `docker`, `terraform`…): if you know the manager's upgrade command and can verify the resolved version, apply the same four-question shape. If you can't verify resolution, make it needs-human rather than guessing — an unverified bump is a PR that claims a fix it may not deliver.
