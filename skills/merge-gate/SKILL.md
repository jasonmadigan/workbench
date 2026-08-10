---
name: merge-gate
description: Pre-merge safety checks. Use when the router is preparing to merge a pull request.
---

# Merge Gate

Pre-merge safety checks. Invoked by the router before any merge.

Read `../../references/dispatch-rules.md` before loading another skill or
asking the user for a decision.

## Check tree

```
Merge request
├── Has the PR been reviewed?
│   ├── No → invoke clawdio:review-coordination first
│   └── Yes → continue
├── Are CI checks passing?
│   ├── No → report failures
│   └── Yes → continue
├── Is the branch behind base?
│   ├── Yes → offer to rebase first through the active user-decision mechanism
│   │         Options: "Rebase and merge", "Merge anyway", "Cancel"
│   │         If rebase: gh pr update-branch or suggest `git rebase origin/main && git push --force-with-lease`
│   └── No → continue
├── Team repo?
│   ├── Yes → team member approved? → merge or flag
│   └── No → merge
└── Never use --admin or --force without explicit user instruction
```

## Check command

```bash
gh pr view <number> --json reviews,statusCheckRollup,reviewDecision,mergeable,mergeStateStatus
```

`mergeStateStatus` values: `CLEAN` (good to go), `BEHIND` (needs rebase), `DIRTY` (conflicts), `BLOCKED` (checks failing or review missing). If `BEHIND` or `DIRTY`, do not merge without asking.

## Merge strategy

**Always use `--squash`** when merging: `gh pr merge <number> --squash --delete-branch`. Do not use `--merge` or `--rebase` unless the user explicitly asks for a different strategy.

## Post-merge cleanup

After merging, if local branch deletion fails because a worktree still exists, clean up:

```bash
git worktree remove <worktree-path> --force 2>/dev/null
git worktree prune
git pull
```
