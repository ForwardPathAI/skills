# Screenshots for UI changes

Read this when the diff changes what a user sees or does. Screenshots show reviewers the real, running result of the PR: captured from the app, embedded in the PR body, and shown in the final response.

## Capture

Pick the smallest set of views that proves the changed behavior, decided from the final diff against the PR's actual base:

- The changed screen and its relevant states (empty, loading, error, open, hover), not a generic home page or a code diff.
- Responsive views when the change touches layout at other widths.
- A before/after pair for a redesign or visual regression. Capture the before view from the base in an isolated checkout (`git worktree add`) when practical; label a missing baseline honestly.

Start the app with the repo's documented startup and fixtures, on the PR branch. Navigate to the affected screen and exercise the changed interaction. Use local or test data fit for the repo's reviewers. Wait for content, fonts, and images to load. Keep before/after views at the same viewport, theme, and data state.

Use the browser, preview, or device tools the agent has, and read any matching browser or computer-use skill or repo screenshot guidance first. In T3 Code, call `preview_status`, then `preview_open` if no automation-capable preview is attached; use another browser only when those tools are absent, fail as unsupported, or the user asks. `preview_snapshot` with `save: true` returns a `screenshotPath`. Every screenshot must exist as a saved file; an inline tool image cannot be attached.

Save files outside tracked source unless the repo names an evidence folder. Name them by scenario (`settings-after-desktop.png`) and record each one's scenario, viewport, and commit. Look at every image: it shows the intended change and is legible, or you retake it. Every image is a faithful capture of observed behavior, never generated or edited.

If the app cannot run or a state cannot be reached, name the exact limit, keep any useful captures, and continue the PR.

**Done when** every changed view has a saved, inspected screenshot, or a named reason it has none.

## Attach

Add a `## Screenshots` section to the PR body, after Summary. Give each image descriptive alt text and a one-line caption saying what it shows; label before/after pairs.

Reviewers need a URL they can open. Upload through a supported GitHub attachment tool or the PR's attachment UI and use the returned URLs; `gh pr create` and `gh pr edit` do not upload local images. If the repo has its own screenshot hosting or committed-evidence convention, follow it. Keep images inside the repo's audience: public gists, unrelated issues, releases, and outside hosts are off limits. Local paths, `file://` links, and temporary preview URLs do not count as attached. If no upload route works, keep the files and report the blocker instead of claiming the PR has screenshots.

If upload needs the PR to exist, open it first, then edit the body. Read the latest body before editing, replace the Screenshots section rather than adding a second one, and pass the body with `--body-file`. Open the rendered PR and confirm the images load at a readable size; a returned URL alone proves nothing.

**Done when** the rendered PR shows every screenshot, or the final response names the attach blocker.

## Keep current

When later fixes change visible behavior, recapture the affected views and replace stale images and captions. Reuse an unchanged screenshot only after checking it still matches the final code.

## Report

Show the screenshots in the final response next to the PR link, using attachment URLs or, where the client renders local files, Markdown images with absolute paths. List any screenshot limits.
