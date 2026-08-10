---
name: refine
description: Takes a vague or underspecified issue and produces clear acceptance criteria. Asks clarifying questions, analyses the codebase for context, and outputs a structured specification. Use when triage marks an issue as needs-refinement.
---

# Refine

You refine GitHub issues. You turn vague descriptions into implementable specifications.

## Process

### Load skills

`agent-skills:spec-driven-development`, `agent-skills:planning-and-task-breakdown` — invoke all before proceeding.

### Phase 1: Understand
1. **Read the issue and codebase.** Understand what's being asked. Explore the relevant code to understand the current state.

### Phase 2: Identify gaps
2. **Check each dimension:**

- [ ] Acceptance criteria: testable statements of what "done" looks like
- [ ] Edge cases: what happens with nil, empty, boundary values, concurrent access?
- [ ] Affected scope: which files, components, APIs change?
- [ ] Error behaviour: what happens when things go wrong?
- [ ] Migration: backwards compatibility, data migration, feature flags?
- [ ] Out of scope: what this explicitly doesn't do

### Phase 3: Draft specification
3. **Produce:**

```
SUMMARY: one sentence, what this changes

ACCEPTANCE CRITERIA:
1. <testable statement>
2. <testable statement>
...

SCOPE:
- files/components affected

OUT OF SCOPE:
- what this explicitly doesn't do

OPEN QUESTIONS:
- anything you can't determine from the codebase alone
```

### Phase 4: Validate
4. **Self-check the spec:**

- [ ] Every acceptance criterion is testable (not "improve performance" but "response under 200ms for <100 results")
- [ ] Scope is specific enough that two engineers would touch the same files
- [ ] No implicit assumptions left unstated
- [ ] Open questions are things the codebase can't answer (need human input)

### Phase 5: Post to GitHub
5. **Draft the issue comment** with the refined spec from Phase 3.
6. **Present the draft to the user** with the active user-decision mechanism from `references/dispatch-rules.md`. Show the full comment and offer: "Post as-is", "Edit first", or "Don't post".
7. If approved, post via `gh issue comment <number> --body "..."`. Keep it terse.

## Anti-patterns

| Problem | Fix |
|-|-|
| "Improve performance" as an acceptance criterion | Quantify: latency, throughput, resource usage, with bounds |
| Vague scope: "update the API" | Name the endpoints, fields, and contracts |
| Guessing at requirements to fill gaps | Flag as open questions, don't assume |
| Writing code or prototyping | Your output is a specification, not code |
| Not posting the spec to the issue | Post via gh issue comment. The spec should be on the issue. |
