# Linear Release Workflow Templates

These templates follow the `PRS-Walmart-PRIME` pattern. Adapt runner labels, checkout versions, and existing build job names to the target repo. Keep the Linear action pinned unless the repo has a documented update policy.

Linear reference: https://linear.app/docs/releases

## Main Branch Sync

Create `.github/workflows/linear-release-main.yml` so each merge to `main` feeds the current in-progress scheduled Linear release.

```yaml
# Sync merges to main into the in-progress Linear release.
# The in-progress release is completed on GitHub Release publish in release.yml.

name: Linear Release (main)

on:
  push:
    branches: [main]

concurrency:
  # Shared with the GitHub Release sync/complete job so a main-push sync never
  # races a release sync/complete on the same Linear pipeline.
  group: linear-release-sync
  cancel-in-progress: false

permissions:
  contents: read

jobs:
  linear-release:
    name: Sync Linear (in-progress release)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Sync issues to current release
        uses: linear/linear-release-action@c0cb8354a362c24c6d3e0948f37fd66d07588e3f # v0.14.5
        with:
          access_key: ${{ secrets.LINEAR_ACCESS_KEY }}
          log_level: verbose
```

## GitHub Release Sync And Complete

Add this job to the workflow that runs on `release.published` and builds/pushes production release artifacts. Put it after every required artifact job succeeds.

```yaml
linear-release:
  name: Sync Linear (customer release)
  needs: [build-release-images]
  if: ${{ !cancelled() && (needs.build-release-images.result == 'success' || (github.event.release.prerelease && needs.build-release-images.result == 'skipped')) }}
  runs-on: ubuntu-latest
  permissions:
    contents: read
  concurrency:
    group: linear-release-sync
    cancel-in-progress: false
  steps:
    - name: Checkout release tag
      uses: actions/checkout@v4
      with:
        fetch-depth: 0
        ref: ${{ github.event.release.tag_name }}

    # Scheduled production pipeline: pushes to main already sync merged issues
    # into the in-progress release. This final sync flushes any issues merged
    # since the last main push and attaches the GitHub Release as a link.
    - name: Sync release issues
      uses: linear/linear-release-action@c0cb8354a362c24c6d3e0948f37fd66d07588e3f # v0.14.5
      with:
        access_key: ${{ secrets.LINEAR_ACCESS_KEY }}
        log_level: verbose
        name: ${{ github.event.release.tag_name }}
        links: |
          ${{ github.event.release.html_url }}
          CI run=${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}

    # Prereleases sync issues and links, but do not complete the customer release.
    - name: Complete release
      if: ${{ !github.event.release.prerelease }}
      uses: linear/linear-release-action@c0cb8354a362c24c6d3e0948f37fd66d07588e3f # v0.14.5
      with:
        access_key: ${{ secrets.LINEAR_ACCESS_KEY }}
        command: complete
        log_level: verbose
        name: ${{ github.event.release.tag_name }}
        links: |
          ${{ github.event.release.html_url }}
          CI run=${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

If the repo already parses tags and exposes `is_prerelease`, use that output for the completion condition, as PRIME does:

```yaml
if: needs.validate-tag.outputs.is_prerelease != 'true'
```

## Optional Dev Deploy Sync

If the repo has a separate dev deploy workflow and the team wants deployed dev changes reflected in the same scheduled release, add a sync-only job after the dev deploy succeeds. Do not complete from this job.

```yaml
linear-release-dev:
  name: Sync Linear (dev deploy)
  needs: [deploy-dev]
  if: needs.deploy-dev.result == 'success'
  runs-on: ubuntu-latest
  concurrency:
    group: linear-release-sync
    cancel-in-progress: false
  permissions:
    contents: read
  steps:
    - name: Checkout
      uses: actions/checkout@v4
      with:
        fetch-depth: 0

    - name: Sync issues to current release
      uses: linear/linear-release-action@c0cb8354a362c24c6d3e0948f37fd66d07588e3f # v0.14.5
      with:
        access_key: ${{ secrets.LINEAR_ACCESS_KEY }}
        log_level: verbose
```

## Linear Setup Checklist

- Create a scheduled release pipeline in Linear settings for the production/customer release.
- Generate the pipeline access key from that Linear release pipeline.
- Store the key as `LINEAR_ACCESS_KEY` in GitHub repository secrets, or add `environment:` to the Linear jobs if the secret is environment-scoped.
- Configure Linear path filters for monorepos so only relevant commits enter the pipeline.
- Ensure PR titles, branch names, merge commits, or commit messages include Linear issue identifiers.

## Common Mistakes

- Using a personal Linear API key instead of the pipeline access key.
- Using a continuous pipeline for this scheduled production-release pattern.
- Completing Linear before container images or other release artifacts publish successfully.
- Completing Linear on prereleases.
- Letting main-push sync and release completion use different concurrency groups.
- Using a shallow checkout, which can hide commits from the action.
- Passing `version` for the scheduled-current-release pattern without intentionally changing the release model.
