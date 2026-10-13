---
name: correctness
description: "Benedict review skill: logic bugs a change introduces, such as wrong results, broken edge cases, inconsistent state, mishandled errors, races and callers the change breaks."
metadata:
  benedict/review: "true"
---

# Correctness

Find behavior the change gets wrong. Before you report, pick a concrete input, run the code in your head and follow it to the line that fails.

## Look for

- **Logic**: inverted or wrong conditions, off-by-one errors, the wrong operator or variable, a processed value computed and then the raw one used.
- **Edge values**: empty strings and collections, `0`, `false`, `null`, `undefined`, negative numbers, the first and last item. Truthiness checks that treat `0` or `""` as missing.
- **State**: shared or default values mutated across calls, caches that are never invalidated, steps run in the wrong order, half-written data left when a later step fails.
- **Errors**: failures swallowed or reported as success, error paths that skip cleanup, promises that are never awaited, retries of an action that must not run twice.
- **Concurrency**: check-then-act races, read-modify-write without a lock or transaction, async callbacks reading state that changed after they were scheduled.
- **Contracts**: a changed signature, return shape, enum value, event name, route, config key or schema that existing callers, consumers or stored data still rely on. Search for them.
- **Types and units**: lossy conversions, integer and float mix-ups, time zones, money rounding, mixed units.

## How to confirm

Read the callers, callees and tests the change touches. A finding names the input or state that triggers it, the line where it goes wrong and the wrong result. If the bug depends on code you have not read, read it or drop the finding.

## Do not report

- Bugs that existed before the change, unless the change makes them reachable or worse.
- Missing validation or error handling when no realistic input fails.
- Effects of a dependency version bump that you cannot see in the code.
- Naming, formatting or other style.
