#!/usr/bin/env python3
"""Lint published skills and repo-local skill wrappers using skill-naming.json."""

import argparse
import json
from pathlib import Path
import re
import sys


NAME_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
SKILL_PATTERNS = (
    "*/SKILL.md",
    ".agents/skills/*/SKILL.md",
    ".claude/skills/*/SKILL.md",
    ".codex/skills/*/SKILL.md",
    ".cursor/skills/*/SKILL.md",
)


def read_name(text):
    """Read a top-level single-line name, not a general-purpose YAML parser."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("missing opening YAML frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError("missing closing YAML frontmatter delimiter") from None
    fields = [line for line in lines[1:end] if re.match(r"^name\s*:", line)]
    if len(fields) != 1:
        raise ValueError("frontmatter must contain exactly one top-level name field")
    value = fields[0].split(":", 1)[1].strip()
    # Names contain no YAML escapes. Accept plain or quoted scalars and comments.
    match = re.fullmatch(
        r"(?:'([^']*)'|\"([^\"]*)\"|([^\s'\"#]+))(?:\s+#.*)?", value
    )
    if not match:
        raise ValueError("name must be a single-line plain or quoted scalar")
    return next(group for group in match.groups() if group is not None)


def load_policy(path):
    policy = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        raise ValueError("policy must be a JSON object")
    for key in ("domains", "actions", "legacy_names"):
        values = policy.get(key)
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError(f"{key} must be a list of strings")
        if len(values) != len(set(values)):
            raise ValueError(f"{key} contains duplicates")
        for value in values:
            if not NAME_PATTERN.fullmatch(value) or len(value) > 63:
                raise ValueError(f"invalid {key} entry: {value!r}")
            if key != "legacy_names" and "-" in value:
                raise ValueError(f"{key} entries must be single words: {value!r}")
    approved = policy.get("approved_names")
    if not isinstance(approved, dict) or any(
        not NAME_PATTERN.fullmatch(name)
        or len(name) > 63
        or not isinstance(reason, str)
        or not reason.strip()
        for name, reason in approved.items()
    ):
        raise ValueError("approved_names must map valid names to nonempty reasons")
    return policy


def lint(root, policy):
    paths = sorted({p for pattern in SKILL_PATTERNS for p in root.glob(pattern)})
    errors = []
    if not paths:
        return paths, ["no SKILL.md files found in the supported skill directories"]
    present = {p.parent.name for p in paths}
    for name in sorted(set(policy["legacy_names"]) - present):
        errors.append(f"skill-naming.json: remove stale legacy exception {name!r}")

    for path in paths:
        label = path.relative_to(root).as_posix()
        folder = path.parent.name
        try:
            name = read_name(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{label}: {error}")
            continue
        if not NAME_PATTERN.fullmatch(name) or len(name) > 63:
            errors.append(f"{label}: name must be lowercase kebab-case, 1-63 characters")
        if name != folder:
            errors.append(f"{label}: name {name!r} must match directory {folder!r}")
        if name in policy["approved_names"] or name in policy["legacy_names"]:
            continue
        parts = name.split("-")
        if (
            len(parts) < 2
            or parts[0] not in policy["domains"]
            or parts[1] not in policy["actions"]
        ):
            errors.append(
                f"{label}: use domain-action[-qualifier], e.g. issue-write or "
                "ui-design-mobile; see skill-naming.json for vocabulary and exceptions"
            )
    return paths, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1],
        help="repository root; defaults to this script's repository",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        policy = load_policy(root / "skill-naming.json")
        paths, errors = lint(root, policy)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Skill naming configuration error: {error}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"Skill naming failed: {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Skill naming passed: {len(paths)} skill entry points checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
