---
name: open-pr-with-screenshots
description: "Open or update a GitHub PR with screenshots of the actual changes. Use whenever authorized implementation or PR work changes user-visible UI, or the user requests PR screenshots or visual evidence, including normal, stacked, and existing PRs."
---

# Open PR with Screenshots

Extend the existing PR workflow with screenshots of the actual running changes, embedded in the PR description and shown in the final response. Invoking this skill to open or update a PR authorizes attaching those screenshots within the user's stated limits.

## When this applies

Apply this skill automatically during authorized PR work whenever the diff changes what a user sees or interacts with: pages, routes, components, styles, themes, layout, responsive behavior, user-facing copy, empty/loading/error states, or client-side interactions. Also apply it when the user explicitly requests PR screenshots or visual evidence.

Decide from the final diff against the PR's actual base, including when updating an existing PR or pushing maintenance fixes that introduce visible changes. When it is unclear whether a change is visible, treat it as UI and capture the affected screen. Skip screenshot capture for changes with no visible effect, such as backend-only logic, data or migration work, infrastructure, CI, tests, docs, and refactors that do not alter rendered output; say briefly in the PR why no screenshots apply when the change touches UI code without a visible effect. Honor an explicit request to skip screenshots.

## Compose the existing workflow

Read and follow [open-pr](../open-pr/SKILL.md) for base selection, branch preparation, validation, commits, pushes, and PR creation, including its tracking-issue requirements unless overridden by the user's instructions. For an explicitly requested stacked PR, use [stack-pr](../stack-pr/SKILL.md) instead, resolving and preserving the actual parent base before branch setup. Reuse a matching existing PR.

Resolve companion skills by name from the current agent's discovered skill locations when they are installed separately rather than beside this skill. If the required publishing skill is unavailable, report the missing dependency and continue independently authorized capture work; do not invent a replacement publication policy. Use the agent's available tools or authenticated `gh` CLI; agent-specific plugins are not prerequisites unless the requested deliverable needs their capabilities.

When implementation is also requested, complete and validate it before capturing evidence. Compose an available `implement` skill when applicable. Treat these as phases of one task: implement once, use the actual PR base, add screenshots, publish once per PR, and maintain the result where authorized. Respect explicit local-only, no-push, and draft-only limits; a request for local screenshots alone does not authorize PR publication.

Integrate screenshot capture after preparing and validating the changes, before publishing the PR description. If attachment upload requires a PR to exist, open it, then add the images before reporting completion. If `maintain-pr` is available and maintenance is authorized, read and follow it; its review requirements and stopping conditions remain authoritative. Otherwise verify publication and evidence, and report that ongoing review maintenance was not performed. Capture and attachment failures do not prevent independent authorized PR work, but remain explicit blockers to completing this screenshot workflow.

When T3 Code exposes `link_pull_request`, register the full URL immediately after creating or beginning work on a PR, including every worked-on stack layer. Before finishing, use `list_thread_pull_requests` and link any missing PR from this work. Report a linking failure accurately.

## Capture evidence of the change

Inspect the diff against the PR's actual base and choose the smallest useful set of views that demonstrates the changed behavior. Show the resulting UI and relevant interaction states, rather than code diffs or a generic home page. Include responsive views when the change affects them. A before/after pair is useful for a visual regression or redesign; capture the before view from the actual base in an isolated checkout when practical. Label an unavailable baseline honestly.

Use the repository's documented app startup and fixtures. Run the intended branch, navigate to the affected screen, and exercise the changed interaction. Prefer local or test data suitable for sharing with the repository's reviewers. Wait for the intended content, fonts, and images to load. Keep comparable before/after views at the same viewport, theme, and data state where possible.

Use available browser, preview, or device tools appropriate to the application. Read the applicable browser or computer-use skill when available before using that surface, and follow repository-specific screenshot guidance. In T3 Code, prefer the collaborative preview when its tools are exposed: call `preview_status` first, and `preview_open` if no automation-capable preview is attached. Use another browser system only when those tools are absent, the user requests it, or `preview_open` explicitly reports unsupported/unavailable. Inspect actionable errors and retry with corrected arguments. `preview_snapshot` with `save: true` returns a real `screenshotPath`; keep that path for attachment and final-response images. An agent without these tools can use its own supported browser or device tools. A tool image without a saved file is insufficient for delivery.

Save screenshots outside tracked source unless the repository already specifies an evidence location. Use descriptive names such as `settings-after-desktop.png`. Record each image's scenario, viewport, and captured commit; note any relevant uncommitted changes. Visually inspect every image to confirm it shows the intended change and is legible. Retake failed captures. Do not generate, reconstruct, or alter screenshots to suggest behavior that was not observed.

If the change has no visible interface, say so and include relevant validation instead of manufacturing a screenshot. If the app cannot run or the affected state cannot be reached, identify the exact limitation, retain any useful evidence, and continue the independent PR work.

## Attach screenshots to the PR

Add a concise Screenshots section to the existing PR template, with descriptive alt text and captions explaining what each image demonstrates. Use before/after labels where applicable. Preserve the problem, resulting behavior, existing relevant issue links, and actual validation results supplied by the PR workflow.

Prefer native GitHub image attachments through a supported upload tool or GitHub's attachment UI. Discover an available upload capability rather than assuming `gh pr create` or `gh pr edit` uploads local images. Use returned attachment URLs in the body. If the repository has an established screenshot hosting or committed-evidence convention, follow it and verify access. Keep images within the repository's intended audience; do not create public gists, unrelated issues, releases, or external hosting just to upload them.

Local filesystem paths, `file://` links, and temporary preview URLs are not reviewer-accessible PR images. If supported attachment or repository-approved hosting is unavailable, keep the saved files and report the attachment blocker; do not claim the PR contains screenshots.

Read the latest PR body before editing it, preserve existing context, and update the screenshot section without adding duplicates. For `gh`, write the exact multiline body to a temporary file and pass `--body-file`. Verify the saved body and inspect the rendered PR to confirm the images load at a readable size for the intended reviewers. A returned URL alone does not establish successful attachment.

## Keep evidence current and finish

After maintenance fixes change visible behavior, recapture the affected views, replace stale images and captions, and verify rendering again. Reuse unaffected screenshots only after checking that they still represent the final implementation. If refreshing screenshot files changes the branch, continue the applicable maintenance checks and latest-commit review requirements.

Finish only when the selected PR workflow's completion rules are satisfied and applicable screenshots represent the final changes and render in the PR, or report the concrete remaining blockers. Distinguish completed technical review from human approval and merge readiness.

When a PR was created or updated, return its link and final head SHA. For local-only work, state that no PR was published. Include concise validation and review status and any screenshot limitations. Show the screenshots using the client's supported image display method or verified attachment URLs, alongside the PR link when one exists. Use Markdown images with absolute file paths only when the client supports displaying local files; otherwise report any remaining display limitation. Do not promise future monitoring, merge, enable auto-merge, or deploy as part of this workflow.
