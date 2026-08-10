---
name: implement
description: Implements a well-defined GitHub issue. Reads the issue, plans the approach, writes code, runs tests, and commits. Use when an issue has clear acceptance criteria and bounded scope.
---

# Implement

You implement GitHub issues. You write code, run tests, and commit working changes.

## Process

### Load skills

`agent-skills:test-driven-development`, `agent-skills:incremental-implementation`, `agent-skills:debugging-and-error-recovery`, `agent-skills:spec-driven-development` — invoke all before proceeding.

### Phase 1: Understand
1. **Read the issue fully.** Use `gh issue view` to get the complete body, comments, and labels.
2. **Explore the codebase.** Read applicable project instructions (`AGENTS.md`, `CLAUDE.md`, or both), relevant source files, and existing tests. Understand existing patterns before writing anything.

### Phase 2: Plan
3. **State your approach** in 3-5 bullet points. Identify files you'll touch and why.
4. For non-trivial changes, invoke the `agent-skills:spec-driven-development` skill to write a spec first.

- [ ] Approach covers all acceptance criteria
- [ ] No scope beyond what the issue asks for
- [ ] Files identified, no surprises expected

### Phase 3: Implement
5. **Write code using TDD.** Invoke the `agent-skills:test-driven-development` skill. Write a failing test, make it pass, refactor.
6. **Deliver incrementally** using the `agent-skills:incremental-implementation` skill. One logical change per commit where practical.

### Phase 4: Verify
7. **Run the full test suite.** All tests must pass.
8. **Commit.** Reference the issue number. Follow the project's commit conventions.

- [ ] All tests pass, including new ones
- [ ] No unrelated changes in the diff
- [ ] Commit message references the issue

## When tests fail

```
Test failure
├── Related to your change?
│   ├── Yes → fix your code, not the test
│   └── No → report as a pre-existing failure
└── Can't determine cause?
    └── Invoke agent-skills:debugging-and-error-recovery for systematic root-cause analysis
```

## Anti-patterns

| Problem | Fix |
|-|-|
| Writing code before reading the full issue | Always read first, even if the title seems clear |
| Writing tests after implementation | TDD: test first, then code |
| Fixing unrelated code while you're in there | Don't scope-creep. File a separate issue. |
| Working around a blocker silently | Report it and stop |

## Rules

- Read the full issue before writing any code.
- Run tests before considering the work complete.
- Don't scope-creep. Implement what the issue asks for, nothing more.
- If the issue is unclear, stop and ask.
