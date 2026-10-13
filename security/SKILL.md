---
name: security
description: "Benedict review skill: vulnerabilities a change introduces that an attacker can reach, such as broken authorization, injection, SSRF, secret exposure, weak crypto and unsafe CI workflows."
metadata:
  benedict/review: "true"
---

# Security

Find vulnerabilities the change introduces that an attacker can actually reach. For each one, know who controls the input, how it reaches the dangerous operation and what they gain.

## Look for

- **Authorization**: code that acts on an ID without checking the caller may access it, queries missing a tenant or owner filter, role checks that only happen in the client.
- **Authentication**: checks that can be bypassed, tokens accepted without verifying signature, expiry or audience, sessions that survive logout or a password change, secrets compared in non-constant time.
- **Injection**: untrusted input reaching SQL, shell commands, file paths, templates, raw HTML, `eval`, NoSQL filters or unsafe deserializers (pickle, YAML load, native object serialization) without parameters or escaping.
- **SSRF**: user input that controls the host or scheme of a server-side request.
- **Secrets**: credentials committed in code, written to logs, returned in responses or errors, or read from the environment with a hardcoded fallback.
- **Data exposure**: responses or logs carrying other users' data, personal data or internal fields; CORS that allows any origin with credentials.
- **Crypto**: weak hashing for passwords, `Math.random` or similar for tokens, disabled TLS verification, hand-rolled crypto.
- **Uploads and files**: path traversal, or uploads that can be executed or overwrite other files.
- **CI and infrastructure**: workflows that run pull request code with secrets, `${{ }}` expressions with attacker-written text inside shell steps, public storage, roles far wider than the job needs.

## Trusted input

Environment variables, CLI flags, server config, constants and responses from your own internal services are not attacker-controlled. Template and query frameworks that escape or parameterize by default are safe unless the code opts out, for example with `dangerouslySetInnerHTML`, `v-html` or SQL built from strings.

## Do not report

- Missing hardening with no concrete attack: rate limits, security headers, generic "validate this input".
- Resource exhaustion, unless a single unauthenticated request triggers it.
- Missing checks in client-side code; report the server endpoint if it lacks them.
- Outdated dependencies; dependency scanners cover them.
- Tests, fixtures, examples and documentation.
