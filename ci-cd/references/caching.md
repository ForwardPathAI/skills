# CI speed and caching

Apply when CI for a Bun + Turborepo repo is slow, or when you add or change install, cache, or Turbo steps. The execution policy and naming contract in [the CI skill](../SKILL.md) still decide which checks run on which event; this reference decides how fast each one runs.

`ForwardPathAI/fp-os` is the worked example: its `turbo.json`, `.github/actions/setup-bun/action.yml`, and `.github/workflows/ci.yml`.

## Install

Run `bun install --frozen-lockfile` with no dependency cache step: no `actions/cache`, `useblacksmith/cache`, or sticky disk for `~/.bun/install/cache` or `node_modules`. In fp-os a cold install took 0–6s, while restoring the Bun cache took 13–16s at first and 31s once `restore-keys` had grown it to 2.3 GB. Docker layer caching (`cache-from` / `cache-to`) is separate and stays.

## Job layout

Run each check as its own single-stage job, in parallel. Each job checks out, calls one shared composite setup action (Bun, install, remote cache), and runs one command. Jobs then cost one setup each instead of serial step time, and wall-clock time becomes the slowest job. Aggregate them in the gate the enforcement contract describes.

## Turbo task cache

Turbo replays a task when its hash matches: the package's tracked files, its `dependsOn` task hashes, `globalDependencies`, declared `env`, and pass-through args. Selection by cache replaces `--affected`, changed-file scripts, and canaries that prove the selector works: a cache skip only happens when inputs match, while a broken selector skips work and still reports green.

- **Cache every check and build.** Checks store logs only (`"outputs": []`). Builds store their artifacts, excluding framework caches: `[".next/**", "!.next/cache/**", "dist/**"]`.
- **Hash internal dependencies with a transit node.** `"transit": { "dependsOn": ["^transit"] }`, then `"dependsOn": ["transit"]` on typecheck, test, and other checks. A dependent's hash then changes when a package it imports changes, while the tasks still run in parallel. A check with no `^` dependency stays green on a stale hash after an internal package changes.
- **List shared root config in `globalDependencies`**: the base tsconfig, the root test config, `bunfig.toml`.
- **Declare every env var that changes a task's result** in that task's `env`. Keep `"envMode": "loose"` until the CI environment is enumerated: strict mode removes undeclared vars from the task's environment and can break it.
- **Give repo-wide suites a root task** (`"//#test:scripts"` plus a root script) with default inputs, which are every tracked file. Use `$TURBO_ROOT$/…` globs only for narrow additions: explicit globs skip `.gitignore`, so local-only files enter the hash and laptop and CI hashes diverge.
- **Split repo-wide checkers into per-package tasks.** Give each package a script that runs the checker on its own project (for example `--project tsconfig.json`), and add the checker's sources to that task's inputs: `"$TURBO_DEFAULT$", "$TURBO_ROOT$/scripts/<checker>/**"`. Add a test asserting every package with a `tsconfig.json` defines the script, since Turbo skips a package that lacks it without error.
- **Pass args in their own invocation.** Args after `--` reach every task in that `turbo run` and enter the hash, so `turbo run test -- --maxWorkers=2` runs alone. CI-only args make CI and laptop hashes differ; move shared flags into the tool's config to share entries.
- **Commit or opt out of Turbo's agent block.** Turbo 2.x writes a managed block into `AGENTS.md` when it detects an agent. Commit it, or set `"agentGuidance": false` in `turbo.json`.

Read the installed version's docs before changing Turbo config: resolve `turbo/package.json` from a workspace that depends on it and open `docs/` beside it.

## Remote cache

Use Vercel Remote Cache. The cache belongs to a Vercel **team**, not a project: create no Vercel projects, and one team serves every repo. Vercel's Hobby plan is for non-commercial use, so put the cache on a team plan.

1. In the Vercel team, open Settings → Build and Deployment → OIDC Policies for CLI Access and add a Turborepo CLI policy for the repository. Leave branches unrestricted so pull request and queue runs read and write.
2. Put the team slug or ID in Infisical as `TURBO_TEAM`, in the repository-scope folder the [infisical](../../infisical/SKILL.md) skill defines.
3. Give the workflow `permissions: { contents: read, id-token: write }`. In the shared setup action, add `vercel/setup-turborepo-remote-cache-action` pinned to its commit SHA, with `team: ${{ secrets.TURBO_TEAM }}` passed as an input and `continue-on-error: true`. It exchanges the job's OIDC token for a short-lived `TURBO_TOKEN`; a fork PR, missing policy, or outage then runs uncached instead of failing.
4. On laptops, `bunx turbo login` then `bunx turbo link` per checkout. `link` writes the gitignored `.turbo/config.json`.

Enable `"remoteCache": { "signature": true }` only after every reader, laptops included, has `TURBO_REMOTE_CACHE_SIGNATURE_KEY`; until then their remote reads fail.

Vercel over the GitHub Actions cache: GitHub scopes cache entries by branch, so main and merge-queue commits cannot read entries a pull request wrote, and laptops cannot share them. With Vercel, a queue commit whose tasks match the pull request's hashes replays them.

## Verify

_Done when_:

1. Every cached task, run twice, reports `FULL TURBO` on the second run.
2. `turbo run <tasks> --dry=json`, compared before and after editing one file in a low-level internal package, changes the hash of that package and every dependent, and leaves unrelated packages unchanged. Editing a `globalDependencies` file changes every hash.
3. The first CI run logs `Remote caching enabled`, and a rerun of the same commit replays its tasks.
