---
name: design-patterns
description: "Benedict review skill: design that breaks the architecture and patterns a codebase already uses, such as layering and dependency direction, module boundaries, a second way of doing something, and patterns misapplied."
metadata:
  benedict/review: "true"
---

# Design patterns

Find code that works against the architecture the repository already has. Learn its patterns first: read `AGENTS.md`, `CLAUDE.md`, the README and any architecture docs, and look at a few neighbors of each changed file.

## Look for

- **Layering**: handlers or components that reach the database or external services directly when the codebase goes through a service or data layer; domain code importing framework or infrastructure code; circular imports between modules.
- **A second way**: a new HTTP client, logger, config loader, error type, state store, validation or date library, or raw `fetch`, beside the one the codebase already uses for that job.
- **Misplaced responsibility**: business rules in a controller, route or UI component; persistence or network calls inside code that the rest of the codebase treats as pure.
- **Coupling**: imports of another module's internals instead of its public interface, new global mutable state, hidden singletons where the codebase passes dependencies in.
- **Misapplied patterns**: a pattern the problem does not need, such as a factory with one product or an event bus for a direct call; or a pattern the codebase uses, applied wrongly, such as a repository that leaks query objects.
- **Written rules**: violations of architecture rules in the repository's agent instructions or docs. Quote the rule.

## How to confirm

Name the existing pattern and point to a file that follows it. Say what it costs: what breaks, what becomes hard to test or what will now change in two places.

## Do not report

- A preference between equally valid designs when the codebase has no established pattern.
- Redesigns beyond the change. Report what the change introduces, not what it inherits.
- Naming, formatting or file layout.
