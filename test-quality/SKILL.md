---
name: test-quality
description: "Benedict review skill: problems with the tests a change adds or should have changed, such as behavior changes with no test, tests that cannot fail, wrong assertions, over-mocking and flaky timing."
metadata:
  benedict/review: "true"
---

# Test quality

Find gaps and mistakes in the tests for the behavior the change adds or alters. Look at neighboring tests to learn what the repository usually tests.

## Look for

- **Untested behavior**: a new or changed branch, error path or contract with no test, where the repository tests that kind of code. Name the case that is not covered.
- **Tests that cannot fail**: no assertion, asserting a mock's own return value or something the setup guarantees, assertions in a callback that never runs, async assertions never awaited.
- **Wrong assertions**: snapshots or expected values updated to match buggy output, expected values copied from the implementation, a test whose name and checks disagree.
- **Over-mocking**: the unit under test, or the logic the test claims to check, is mocked away.
- **Flakiness**: real clocks, sleeps, randomness, network calls, shared state between tests or dependence on test order.
- **Removed coverage**: tests deleted, skipped or weakened without a reason the change explains.

## Do not report

- Coverage percentages. Ask for a test only where a regression could plausibly slip through.
- Test naming, style or structure.
- Missing tests for trivial code, such as getters, wiring or config.
