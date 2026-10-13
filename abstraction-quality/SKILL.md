---
name: abstraction-quality
description: "Benedict review skill: abstractions a change adds or changes that are leaky, shallow, premature or misleading, such as wrappers that add nothing, functions doing several jobs, boolean mode flags, and names or types that misstate behavior."
metadata:
  benedict/review: "true"
---

# Abstraction quality

Find new or changed functions, classes, modules, components and types whose shape makes the next change harder or easier to get wrong.

## Look for

- **Leaky**: callers have to know the internals to use it, such as a call order, a field to set first or an implementation error to catch; it returns types from the library it is meant to hide.
- **Shallow**: wrappers, classes or interfaces that only forward to one thing and hide nothing; an interface with one implementation and no need for a seam.
- **Speculative**: generic parameters, options, hooks or config for cases no caller has.
- **Several jobs**: a function or component that fetches, transforms, renders and saves; boolean or mode parameters that switch between different behaviors; deep nesting that hides which branch runs.
- **Misleading contract**: a name that says something other than what the code does, such as `getX` that writes or `isValid` that throws; types that allow invalid states, such as optional fields that are always set together, strings with a known set of values, or `any` and casts that discard checked types.
- **Mixed levels**: low-level details such as string parsing or SQL inside high-level workflow code, or a public API that exposes details callers should not depend on.

## How to confirm

Point to a concrete cost: a caller that already works around it, a bug it makes easy or a future change that would need edits in several places. Suggest the simpler shape.

## Do not report

- Taste on its own: naming style, file length or function length.
- Abstractions that existed before and that the change only uses.
- A little clear duplication where an abstraction would be worse.
