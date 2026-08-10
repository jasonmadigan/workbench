---
name: parallel-ship
description: Dispatches multiple worktree-workers for multi-issue shipping. Use when the router receives multiple issue references in one ship request.
---

# Parallel Ship

Dispatches multiple worktree-workers in parallel for multi-issue ship. Invoked by the router when multiple issues are referenced.

Read `../../references/dispatch-rules.md` before dispatching or asking the user
for a decision. In particular, do not run concurrent writers without isolated
worktrees.

## Step 1: Confirm scope and PR type

**Non-negotiable:** always use the active client's user-decision mechanism here, even if the user already said "ship" or "yes". The confirmation step cannot be skipped. Ask:
1. "Ship these N issues in parallel?" with options to proceed or adjust.

PRs default to draft. Only pass `--ready` if the user explicitly asks for ready-for-review PRs.

## Step 2: Dispatch in parallel

Invoke `clawdio:worktree-recovery` first to check for in-progress work.

Spawn all logical `worktree-worker` agents simultaneously through the active client adapter. Each gets:
- a separate, verified git worktree
- the worktree's absolute path and an instruction to use it as the working directory for every command when isolation was created manually
- The issue reference (URL or number)
- The repo context
- `--ready` in the prompt only if the user explicitly asked for ready-for-review PRs

Claude Code may provide worktree isolation directly. In Codex, use native
worktree isolation when exposed; otherwise create one worktree per issue before
dispatch and verify each worker's `git rev-parse --show-toplevel` result. If
isolation cannot be established, run the workers serially.

## Step 3: Collect results

Each worktree-worker outputs a structured result (RESULT/PR_URL/BRANCH/ISSUE). Collect all results and present as a summary table:

```
| Issue | Result | PR | Branch |
|-|-|-|-|
| #10 | complete | #45 | 10-add-feature |
| #11 | blocked | -- | -- |
| #12 | complete | #46 | 12-fix-bug |
```

## Step 4: Offer next steps

Through the active user-decision mechanism:
- "Review all PRs" → invoke `clawdio:review-coordination` on each successful PR
- "Review PR #N" → review a specific one
- "Done for now" → stop

For any blocked results, report the reason and offer to retry or skip.
