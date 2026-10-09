# Skill naming

When adding or renaming a skill:

- Use `domain-action[-qualifier]`, such as `pr-open`, `issue-refine`, or `ui-design-mobile`.
- Use lowercase kebab-case, at most 63 characters. The skill directory and frontmatter `name` must match exactly.
- Choose the domain and action from [skill-naming.json](skill-naming.json). Use `issue`, not `ticket`, and verbs such as `write` or `refine`, not `writer` or `refiner`.
- Name the responsibility. Put input formats, output destinations, providers, and implementation details in the description unless they distinguish a real variant.
- Keep `prototype` and `setup-fp-skills` as approved exceptions. Do not rename existing skills just to satisfy this convention.
- `legacy_names` is the migration list for existing names, not a way to bypass the rule for new skills. Remove an entry when its last skill directory is removed or renamed. Add a domain, action, or approved exception only with a documented reason in the change.
- A rename includes the folder, frontmatter, callers, README, install commands, and local wrappers. Keep compatibility names only as wrappers around the canonical skill.

Run `python3 scripts/lint_skill_names.py` after adding, removing, or renaming skills. When changing the linter or policy, also run `python3 -m unittest discover -s tests -p 'test_skill_names.py'`.

The linter enforces spelling, directory matching, vocabulary, and explicit exceptions. Reviewers still check whether the name accurately describes the skill's responsibility.
