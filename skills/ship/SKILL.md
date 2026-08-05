---
name: ship
description: Full lifecycle skill for shipping an issue. Implements, pushes, creates PR, self-reviews, addresses issues, and prepares for merge. Use when the user says "ship this" or "ship #42".
---

# Ship

End-to-end lifecycle for shipping an issue to a merged PR.

## Arguments

Passed via the Skill tool's `args` string. Parse the following:

| Arg | Form | Example |
|-|-|-|
| issue ref | positional or `--issue` | `ship #42`, `ship --issue https://github.com/org/repo/issues/42` |
| `--resume` | flag | Resume an in-progress workflow from memory |
| `--skip-review` | flag | Skip the self-review phase |
| `--ready` | flag | Create PR as ready for review instead of draft |

If no issue ref is provided and no `--resume`, ask the user.

**Multiple issues:** if the user passes multiple issue refs ("ship #10, #11, #12"), do not handle this yourself. Tell `agents/router.md` to use parallel worktree dispatch via `agents/worktree-worker.md` instead. Ship handles one issue at a time.

## State file

Write `.clawdio-state` in the working directory after every phase transition (same format as worktree-worker). This is how the workflow tracks progress and enables resume.

```bash
cat > .clawdio-state << 'STATEEOF'
phase: <current phase>
issue: <issue ref>
branch: <branch name>
pr: <PR URL or "pending">
started: <ISO timestamp of first state write>
updated: <ISO timestamp of this write>
error: <error message if blocked, otherwise empty>
STATEEOF
```

Do NOT git-commit this file. It is orchestrator-internal.

## Resume

Before starting a new workflow, check for existing state in this order:

1. Check for `.clawdio-state` in the current directory

If state is found:
- If `--resume` was passed, resume from the recorded phase
- Otherwise, tell the user about the existing workflow and offer: "Resume from phase N" or "Start fresh"

**If no state file exists but `--resume` was passed**, infer the current phase from observable state:

```bash
# are there commits ahead of main?
COMMITS=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")

# does a PR exist for this branch?
BRANCH=$(git branch --show-current)
PR=$(gh pr list --head "$BRANCH" --json number,url,isDraft --jq '.[0]' 2>/dev/null)

# what's the CI status?
PR_NUM=$(echo "$PR" | jq -r '.number // empty' 2>/dev/null)
CI=$(gh pr view "$PR_NUM" --json statusCheckRollup --jq '[.statusCheckRollup[] | {name: .name, conclusion: .conclusion}]' 2>/dev/null)
```

| Observable state | Inferred phase | Resume action |
|-|-|-|
| No commits ahead of main | Not started | Start from Phase 1 |
| Commits ahead, no PR | Pre-push | Resume at Phase 4 (push and PR) |
| PR exists, CI not run or running | CI pending | Resume at Phase 5 (CI check) |
| PR exists, CI failed | CI failed | Report failures, offer to fix |
| PR exists, CI passed, draft | Ready | Offer to mark ready for review |
| PR exists, CI passed, not draft | Complete | Report done |

Report the inferred state to the user before proceeding.

## Process

### Phase 1: Implement

1. Update the issue state: assign to user and add "in-progress" label (per `clawdio:issues` lifecycle).
   ```bash
   gh issue edit <number> --add-assignee "@me" --add-label "in-progress"
   ```
2. Dispatch the implement agent using `subagent_type: "clawdio:implement"`. Wait for completion.

- [ ] All tests pass
- [ ] Implementation matches acceptance criteria
- [ ] No scope creep

**Diff gate:** verify the agent produced changes before proceeding.

```bash
COMMITS=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
CHANGES=$(git status --porcelain)
```

If `COMMITS` is 0 AND `CHANGES` is empty: STOP. Report "implementation produced no code changes -- the implement agent may have failed." Comment on the issue (per `clawdio:issues`), remove "in-progress" label, write state with `phase: blocked`. Do not proceed.

```bash
gh issue comment <number> --body "Blocked: implement agent produced no code changes."
gh issue edit <number> --remove-label "in-progress"
```

**Write `.clawdio-state`:** `phase: pre-ship`

### Phase 2: Pre-ship checks

2. Check if any files in `agents/`, `skills/`, or `hooks/` were changed:
   ```bash
   git diff --name-only origin/main..HEAD | grep -E '^(agents/|skills/|hooks/)'
   ```
   If matches found, invoke `clawdio:doc-sync` to verify and fix documentation.
3. Invoke `agent-skills:shipping-and-launch` for pre-ship checklist.
4. Invoke `agent-skills:git-workflow-and-versioning` for commit conventions.

- [ ] Docs are in sync (if agent/skill/hook files changed)
- [ ] Pre-ship checklist passes
- [ ] Commits follow conventions

**Write `.clawdio-state`:** `phase: reviewing`

### Phase 3: Self-review

Skip this phase if `--skip-review` was passed.

5. Review the changes locally before pushing. Tell the router to dispatch specialist reviewers (code-reviewer, test-verifier, and any domain specialists) against the local diff (`git diff origin/main..HEAD`).
6. If the review found real issues (Critical or Important), fix them. Commit.

- [ ] All Critical findings addressed
- [ ] All Important findings addressed
- [ ] Nits addressed if trivial, skipped if contentious

**Write `.clawdio-state`:** `phase: pushing`

### Phase 4: Push and PR

7. Create a branch if not already on one:
   ```bash
   git checkout -b <issue-number>-<short-description>
   ```
8. Push: `git push -u origin HEAD`
9. Create the PR via `gh pr create --draft` following the clawdio:pr-description skill format. Link the issue with `Closes #N` in the body. Draft is the default. Only omit `--draft` if `--ready` was passed.

- [ ] PR description follows template (summary, linked issue, test evidence)
- [ ] Branch name is descriptive (`<issue-number>-<short-description>`, not a system-generated name)
- [ ] PR is draft (unless --ready was explicitly passed)

**Write `.clawdio-state`:** `phase: ci-check`, include `pr: <url>`

### Phase 5: CI check

10. Check the status of CI checks on the PR:
    ```bash
    gh pr checks <number> --watch --fail-fast
    ```
    If `--watch` is available and checks are still running, this blocks until they complete. If `--watch` is not supported, poll with:
    ```bash
    gh pr view <number> --json statusCheckRollup --jq '[.statusCheckRollup[] | {name: .name, status: .status, conclusion: .conclusion}]'
    ```

11. If CI fails: report the failing checks, read the logs (`gh run view <run-id> --log-failed`), and offer to fix. Do not mark as ready for review.
12. If CI passes: report success. The PR is ready to be marked for review.
13. If CI is still running and has been for more than 5 minutes: report current status and tell the user to check back later or use `gh pr checks <number> --watch`.

- [ ] CI checks have completed
- [ ] All required checks pass
- [ ] If checks failed, failures reported with log excerpts

**Write `.clawdio-state`:** `phase: complete`

### Phase 6: Report

14. Tell the user: PR is ready for team review. Link to the PR. Include CI status.
15. Delete `.clawdio-state`.

## Decision tree: merge or wait?

```
PR ready
├── Personal repo + user said "ship and merge"?
│   └── Run `gh pr merge --squash`
├── Personal repo + user didn't say to merge?
│   └── Report PR link, let user decide
└── Team repo?
    └── Never merge automatically. Report PR link.
```

## Anti-patterns

| Problem | Fix |
|-|-|
| Merging on a team repo without asking | Never. The user decides after team review. |
| Skipping self-review | Always self-review unless `--skip-review`. Catches obvious issues before team sees them. |
| Pushing without running tests | Tests must pass before `git push`. |
| Creating a PR with a one-line description | Follow `skills/pr-description/SKILL.md` format. |
| Proceeding to push after implement produced nothing | Diff gate catches this. Check `git status --porcelain` before advancing. |
| Not checking for existing workflow state | Always check `memory/workflow_ship_*.md` for in-progress workflows before starting fresh. |
