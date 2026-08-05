---
name: address-feedback
description: Reads review comments on a PR and fixes the issues raised. Commits and pushes the fixes. Use after a PR review has been posted with requested changes.
---

# Address Feedback

You fix PR review comments. You read the feedback, make the changes, and commit.

## Process

1. **Load skills:** `agent-skills:debugging-and-error-recovery`, `agent-skills:incremental-implementation`, `agent-skills:git-workflow-and-versioning` — invoke all before proceeding.

2. **Fetch the review.** Use `gh pr view` and the GitHub MCP to get all review comments, inline comments, and conversation threads.

3. **Categorise each comment using the decision tree:**

```
Review comment
├── Specific code change requested?
│   └── Yes → ACTIONABLE: fix it
├── Question asking for clarification?
│   └── Yes → QUESTION: answer in commit message or code comment (only if why is non-obvious)
├── Style preference, minor suggestion?
│   ├── Trivial to fix → NITPICK: fix it
│   └── Contentious or subjective → NITPICK: skip, note why
└── Suggests a different approach entirely?
    └── DISAGREEMENT: flag for the user to decide
```

4. **Fix.** Make the changes. For complex fixes, invoke `agent-skills:debugging-and-error-recovery` for systematic root-cause analysis. Run tests after every change. Commit with a message referencing the review (e.g. "fix nil check per review feedback").

5. **Report.** Present a summary:

```
FIXED:
- <file:line> <what you changed>

SKIPPED (with reason):
- <comment> — <why you skipped it>

NEEDS YOUR INPUT:
- <comment> — <why you can't decide>
```

## Verification

- [ ] All actionable comments addressed
- [ ] Tests pass after changes
- [ ] No unrelated changes in the diff
- [ ] Disagreements flagged, not silently resolved

## Anti-patterns

| Problem | Fix |
|-|-|
| Refactoring adjacent code while fixing feedback | Fix what's asked, nothing more |
| Blindly applying a suggestion that would break something | Explain why it would break, flag for user |
| Marking review conversations as resolved | That's the reviewer's call, not yours |
| Committing without running tests | Tests after every change, no exceptions |
