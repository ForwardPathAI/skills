---
name: speclang-writer
description: Turn a plan into a SpecLang specification — a structured, natural-language Markdown document (the single source of truth) that captures a system's behavior and its pinned implementation details so an AI toolchain or executor can generate the code from the spec, not from the chat. Use when the user says "write a speclang doc", "generate a spec from this plan", "turn this plan into a SpecLang document", "spec-driven development", or wants a natural-language spec that still carries implementation detail.
disable-model-invocation: true
---

# SpecLang Writer

A plan is a sequence of steps to *do*; a SpecLang spec is a description of what the system *is* and how it *behaves*, written so the spec — not the code — is the artifact you maintain. This skill reads a plan (ideally one already hardened by [plan-refiner](../plan-refiner/SKILL.md)) and produces a SpecLang document: "prose code" that a strong model or an AI toolchain can compile into an implementation, with the implementation details the plan pins carried through as explicit constraints.

You have codebase access, internet search, and the user. Ground every claim in the plan and the code it targets; ask the user only for decisions that are genuinely theirs.

## What SpecLang is (and where it comes from)

SpecLang is a **[GitHub Next](https://githubnext.com/projects/speclang/) research project (Nov 2023)** — an attempt to develop software in natural language and let an AI-powered toolchain manage the implementation. Google's **Antigravity** promotes the same paradigm under the name **Spec-Driven Development (SDD)**: a structured specification is the **Single Source of Truth (SSOT)** that AI agents consume to generate, verify, and refine the codebase, so engineers shift from "code writers" to "system architects." This skill writes the SpecLang-format spec that both approaches center on. (If someone attributes SpecLang itself to Google, gently note the real provenance — the format below is the substance either way.)

Two ideas define it:

- **The spec is the source of truth.** The generated code is secondary and rarely inspected by hand. What you maintain is the spec.
- **"Prose code," not "no code."** It is a natural-language representation of computational behavior that still requires you to think like a programmer. It is not a wizard or an app builder.

## The SpecLang format

A SpecLang spec is a **structured, Markdown-like document** written in **only the necessary level of detail**. The detail level varies deliberately across the document — from an offhand remark that implies a dozen lines of boilerplate, to the exact steps of a handshake protocol.

### Document structure

```markdown
# AppName

One or two sentences: what this system is and what it does.

## Screens            ← an H2 groups units of the same kind

### Home Page         ← an H3 is one named unit
Displays a list of trending posts.

- **Behavior:** Fetches and updates the posts from the API.
- **Layout:** Contains a `Header` and a `PostList`.

## Components

### Header
Displays the app title and a refresh button.

- **Behavior:** On tap, triggers the `PostList` to refresh the posts.
- **Styling:** Fixed at the top, large font, background color.
```

Structural conventions:

- **H1 = the system**, followed by a one/two-line summary of what it is.
- **H2 = a group of like units.** Choose groups that fit the artifact: for a UI, `## Screens` and `## Components`; for a service, `## Endpoints`, `## Data model`, `## Jobs`, `## Integrations`; add an `## Overview` when intent needs stating up front.
- **H3 = one named unit** (a screen, component, endpoint, entity, job). Give it a real name and a one-line description.
- **Bold-labeled bullets** carry the unit's facets. The canonical labels are `**Behavior:**`, `**Layout:**`, and `**Styling:**`; extend as needed with `**Data:**`, `**State:**`, `**Inputs:**`, `**Errors:**`, `**Implementation:**`.
- **Cross-reference units in backticks** (`` `PostList` ``) so the reader — and the toolchain — can link them.
- **Nested bullets structure behavior** the way you think about it (see below).
- **`$variable` notation** names values referenced across a description (`$progress`, `$errors`).

### Structuring behavior

When behavior matters, lay out its pieces as nested bullets — inputs, data shapes, conditionals as `if X then Y`, and outcomes — while glossing over *how* to carry it out:

```markdown
- Continuously poll the server for progress on `/progress?taskId=$id`.
  - The server responds with a JSON object with fields:
    - progress: number
    - output: string
    - errors: string
    - If the object is empty, then $progress = 0 and $output/$errors are empty strings.
  - Display $progress as a blue progress bar.
  - If $errors is not empty, display it in a big red box labelled "Task errors:".
  - Display $output in a big gray box labelled "Task output:".
- When $progress reaches 100%, redirect to `/success?taskId=$id`.
```

### Writing style

- **Natural-language prose, structured with Markdown.** Write as if instructing a competent developer: state intent and behavior, leave the obvious plumbing implied.
- **Describe *what*, gloss *how*** — unless the *how* is a real requirement (a protocol, an algorithm, a chosen library). Then spell it out.
- **Only the necessary level of detail.** Don't spec idiomatic choices the model would get right anyway; do spec anything non-obvious or non-negotiable.

### Where implementation details go

SpecLang lets you say not just *what* the system does but *how* you want it built — framework, architecture, patterns, versions — wherever you care. Carry the plan's pinned decisions into the spec as explicit constraints, not as code:

- Global or cross-cutting choices → an `## Overview` or a `## Constraints` section ("Vanilla JavaScript only — no external frameworks"; "Use `pdfplumber` 0.11, already pinned in `requirements.txt`").
- Unit-specific choices → an `**Implementation:**` bullet on that H3 ("**Implementation:** back this with the existing `useQuery` hook in `src/lib/api.ts`").
- **Byte-exact values** the implementation must reproduce (IDs, tokens, route strings, config keys, enum values) → write them **literally** in the spec; never paraphrase or approximate them.

## Prerequisites

- The plan file path (ask if not given — typical locations: the path the user references, `.cursor/plans/`, or a workspace markdown file).
- Read access to the codebase the plan targets, so implementation constraints and cross-references are real, not guessed.

## Workflow

Copy this checklist and track progress:

```
- [ ] Step 1: Load the plan and its context
- [ ] Step 2: Extract behavior and implementation intent
- [ ] Step 3: Choose the spec's structure
- [ ] Step 4: Set the level of detail per unit
- [ ] Step 5: Write the SpecLang document
- [ ] Step 6: Self-check against the SpecLang bar
- [ ] Step 7: Report
```

### Step 1: Load the plan and its context

Read the whole plan. Then read the files, symbols, and paths it cites — you cannot pin an implementation constraint or a cross-reference you haven't seen. Note the plan's intent and any verbatim user requirements; these must survive into the spec.

### Step 2: Extract behavior and implementation intent

Separate two layers as you read:

- **Behavior / intent** — the observable outcomes: what each surface does, its inputs and outputs, its states, its error and edge cases.
- **Implementation detail** — the *how* the plan pins down: libraries and versions, file/module layout, data shapes, algorithms, protocols, and any exact identifiers.

Flag every **byte-exact value** (IDs, tokens, route strings, config keys) to reproduce literally later.

### Step 3: Choose the spec's structure

Pick the H2 groups that fit the system (Screens/Components, or Endpoints/Data model/Jobs/Integrations, etc.). List the H3 units under each. Decide the cross-references between units and name them in backticks. Add `## Overview` and/or `## Constraints` if global intent or global implementation choices need stating once.

### Step 4: Set the level of detail per unit

For each unit, decide where it sits on SpecLang's detail spectrum:

- **Idiomatic / boilerplate** → one offhand line; let the model infer the rest.
- **Behavior-critical** (protocols, state machines, error rules, data contracts) → nested bullets with `if/then` rules, `$var` fields, and exact data shapes.
- **Implementation-pinned** → an explicit `**Implementation:**` bullet or a `## Constraints` entry stating the decision and, briefly, why.

### Step 5: Write the SpecLang document

Write a **new** file — a spec is a distinct artifact from the plan, so do not overwrite the plan. Default path: a sibling of the plan named `<plan-basename>.spec.md` (confirm or take a path if the user gave one). Follow the format above: H1 system + summary, H2 groups, H3 units, bold-labeled bullets, nested behavior, backtick cross-references, `$var` notation. Keep exact identifiers literal. Preserve the plan's intent and verbatim requirements.

Then **link the plan to the spec** so an executor sees it on first read: insert a short blockquote callout at the top of the plan body (directly under its H1, leaving the rest of the plan untouched) stating that the spec at `<spec path>` is the single source of truth for implementation, that every file must be authored from the spec, and that the spec's pinned values must be reproduced byte-exact. Example:

```markdown
> **Executor: read the SpecLang spec first.** The single source of truth for this
> implementation is `<spec path>`. Author every file from that spec, keeping its
> pinned values byte-exact. This plan is the overview; the spec is the contract.
```

### Step 6: Self-check against the SpecLang bar

Verify against the [bar](#speclang-readiness-bar) below before reporting.

### Step 7: Report

Summarize for the user: the spec file path, its top-level structure, which decisions were pinned as implementation constraints vs. left idiomatic, and any gaps recorded as open questions.

## Decision table

| Situation | Action |
|---|---|
| The plan is vague or leans on judgment | Refine it first with [plan-refiner](../plan-refiner/SKILL.md), then spec the hardened plan. |
| A behavior is idiomatic and low-risk | State it in one line; don't over-specify what the model gets right by default. |
| A behavior is a real contract (protocol, data shape, error rule) | Spell it out with nested bullets, `$var` fields, and `if/then` rules. |
| The plan pins a library, version, or architecture | Record it as an `**Implementation:**` bullet or a `## Constraints` entry — a decision, not a suggestion. |
| A value must be reproduced byte-for-byte | Write it literally in the spec; never paraphrase an ID, token, route, or config key. |
| A cited path/symbol can't be verified in the codebase | Note it as an open question rather than asserting it. |
| The system is large | Use fine-grained units (SDD's modular granularity) so each H3 stays small and self-contained. |

## Anti-patterns

- Pasting code blocks as the spec's body — SpecLang is prose that describes behavior, not the implementation itself.
- Over-specifying idiomatic choices the model would make correctly, drowning the real requirements.
- Under-specifying a genuine contract (data shape, protocol, error rule) that the executor must not guess.
- Turning a pinned decision back into a suggestion ("consider using…") instead of stating it.
- Approximating an exact identifier, route, or config value that must be reproduced verbatim.
- Overwriting or rewriting the plan file — the spec is a separate artifact; the only permitted plan edit is the executor callout under its H1.
- Writing the spec but leaving the plan without the executor callout — an executor who opens the plan first must be pointed at the spec.
- Inventing a file path, symbol, or version you didn't verify.

## SpecLang readiness bar

Before finishing, the spec must pass:

- [ ] H1 names the system and summarizes it in a line or two.
- [ ] Units are grouped under H2s and each H3 has a name, a one-line description, and behavior.
- [ ] Behavior-critical units use nested bullets, `$var` notation, and `if/then` rules; idiomatic ones stay terse.
- [ ] Every pinned implementation decision from the plan appears as an explicit constraint, with a reason where non-obvious.
- [ ] Exact identifiers (IDs, tokens, routes, config keys) are literal, not paraphrased.
- [ ] Cross-referenced units are named in backticks and actually exist in the spec.
- [ ] The plan's intent and verbatim requirements survived into the spec.
- [ ] The spec is a new file; the plan body is unchanged except for the executor callout inserted under its H1, pointing at the spec.

## Additional resources

- The SpecLang concept and canonical examples: [GitHub Next — SpecLang](https://githubnext.com/projects/speclang/)
- Google's spec-driven paradigm (spec as Single Source of Truth): [Spec-Driven Development in Antigravity](https://codelabs.developers.google.com/codelabs/getting-started-with-spec-driven-development-in-antigravity)
- Harden the plan into unambiguous statements before spec'ing it: [plan-refiner/SKILL.md](../plan-refiner/SKILL.md)
- Turn the spec into agent-ready Linear issues: [issue-writer/SKILL.md](../issue-writer/SKILL.md)
