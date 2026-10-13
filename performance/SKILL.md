---
name: performance
description: "Benedict review skill: changes that make code slower or heavier at realistic data sizes, such as N+1 queries, unbounded reads, quadratic loops, repeated work, leaks and blocking calls on hot paths."
metadata:
  benedict/review: "true"
---

# Performance

Find changes whose cost grows with data or traffic in a way that will hurt.

## Look for

- **Data access**: a query or request per item in a loop, reads with no limit or pagination, whole tables loaded to filter in memory, new query patterns with no index when the schema is visible.
- **Algorithms**: nested loops or repeated linear searches over collections that grow with users or data, where a map or set lookup would do.
- **Repeated work**: the same expensive call, parse or request made per item or per render when it could run once.
- **Growth and leaks**: caches, maps, queues or listeners that only grow; timers, subscriptions and connections that are never released.
- **Blocking**: synchronous I/O or heavy computation on a request or UI thread; independent slow calls awaited one after another on a hot path.
- **Payloads**: fetching or sending far more data than the code uses.
- **Frontend**: effects that refetch on every render, new object or function identities passed into large memoized lists.

## How to confirm

Say how large the input realistically gets and where the code runs: per request, per item, in a job or once at startup.

## Do not report

- Micro-optimizations with no noticeable effect.
- Code that runs once, at startup, in scripts or tests, or on small fixed-size data.
- Suggestions to add caching without showing repeated expensive work.
