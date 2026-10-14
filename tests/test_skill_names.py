"""Exercise the naming CLI against temporary skill repositories."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


LINTER = Path(__file__).resolve().parents[1] / "scripts" / "lint_skill_names.py"


class SkillNamingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = {
            "domains": ["pr", "issue", "ui"],
            "actions": ["open", "write", "design"],
            "approved_names": {
                "prototype": "Approved short workflow name.",
                "setup-fp-skills": "Stable team entry point.",
            },
            "legacy_names": [],
        }

    def skill(self, folder, name=None, contents=None):
        path = self.root / folder / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        name = name if name is not None else Path(folder).name
        path.write_text(
            contents if contents is not None else f"---\nname: {name}\ndescription: Test\n---\n",
            encoding="utf-8",
        )
        return path

    def run_lint(self):
        (self.root / "skill-naming.json").write_text(json.dumps(self.policy))
        return subprocess.run(
            [sys.executable, str(LINTER), "--root", str(self.root)],
            capture_output=True, text=True, check=False,
        )

    def test_convention_qualifiers_and_approved_short_names(self):
        for name in ["pr-open", "issue-write", "ui-design-mobile", "prototype", "setup-fp-skills"]:
            self.skill(name)
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("5 skill entry points", result.stdout)

    def test_rejects_reversed_unknown_and_actor_names(self):
        for name in ["open-pr", "ticket-write", "issue-writer", "issue"]:
            with self.subTest(name=name):
                path = self.skill(name)
                result = self.run_lint()
                self.assertEqual(result.returncode, 1)
                self.assertIn("domain-action[-qualifier]", result.stderr)
                path.unlink()

    def test_rejects_invalid_spelling_and_length(self):
        for name in ["PR-open", "pr_open", "pr--open", "pr-open-", "ui-design-" + "a" * 54]:
            with self.subTest(name=name):
                path = self.skill(name)
                result = self.run_lint()
                self.assertEqual(result.returncode, 1)
                self.assertIn("lowercase kebab-case, 1-63", result.stderr)
                path.unlink()

    def test_exceptions_do_not_bypass_directory_matching(self):
        self.skill("prototype", name="setup-fp-skills")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("must match directory 'prototype'", result.stderr)

    def test_legacy_exemption_is_exact(self):
        self.policy["legacy_names"] = ["open-pr"]
        self.skill("open-pr")
        self.assertEqual(self.run_lint().returncode, 0)
        self.skill("open-pr-new")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("open-pr-new/SKILL.md", result.stderr)

    def test_removing_or_renaming_legacy_skill_requires_policy_cleanup(self):
        self.policy["legacy_names"] = ["open-pr"]
        self.skill("pr-open")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("remove stale legacy exception 'open-pr'", result.stderr)

    def test_checks_local_wrappers_without_forbidding_shared_names(self):
        self.skill("pr-open")
        for provider in [".agents", ".claude", ".codex", ".cursor"]:
            self.skill(f"{provider}/skills/pr-open")
        self.assertEqual(self.run_lint().returncode, 0)
        self.skill(".agents/skills/pr-open", name="issue-write")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn(".agents/skills/pr-open/SKILL.md", result.stderr)

    def test_frontmatter_requires_one_name_and_both_delimiters(self):
        examples = [
            ("name: pr-open\n", "opening"),
            ("---\nname: pr-open\n", "closing"),
            ("---\ndescription: Test\n---\n", "exactly one"),
            ("---\nname: pr-open\nname: issue-write\n---\n", "exactly one"),
            ("---\nname: |\n  pr-open\n---\n", "lowercase kebab-case"),
        ]
        for contents, diagnostic in examples:
            with self.subTest(contents=contents):
                self.skill("pr-open", contents=contents)
                result = self.run_lint()
                self.assertEqual(result.returncode, 1)
                self.assertIn(diagnostic, result.stderr)

    def test_accepts_quoted_names_and_inline_comments(self):
        for value in ["pr-open # comment", "'pr-open'", '"pr-open" # comment']:
            with self.subTest(value=value):
                self.skill("pr-open", name=value)
                result = self.run_lint()
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_repository_fails(self):
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no SKILL.md files", result.stderr)

    def test_invalid_policy_reports_configuration_error(self):
        self.skill("pr-open")
        self.policy["approved_names"] = {"prototype": ""}
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("configuration error", result.stderr)


if __name__ == "__main__":
    unittest.main()
