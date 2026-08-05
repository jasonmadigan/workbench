---
name: parallel-ship
description: Dispatches multiple worktree-workers in parallel for multi-issue ship. Invoked by the router when multiple issues are referenced.
---

# Parallel Ship

Dispatches multiple worktree-workers in parallel for multi-issue ship. Invoked by the router when multiple issues are referenced.

## Step 1: Confirm scope and PR type

**Non-negotiable:** always use `AskUserQuestion` here, even if the user already said "ship" or "yes". The confirmation step cannot be skipped. Ask:
1. "Ship these N issues in parallel?" with options to proceed or adjust.

PRs default to draft. Only pass `--ready` if the user explicitly asks for ready-for-review PRs.

## Step 2: Dispatch in parallel

Invoke `Skill(clawdio:worktree-recovery)` first to check for in-progress work.

Spawn all worktree-worker agents simultaneously in a single message. Each gets:
- `subagent_type: "clawdio:worktree-worker"`
- `isolation: "worktree"` (Claude Code creates a separate worktree per agent)
- The issue reference (URL or number)
- The repo context
- `--ready` in the prompt only if the user explicitly asked for ready-for-review PRs

See `references/dispatch-rules.md` for dispatch rules.

Example for three issues (default draft mode):

```
Agent(subagent_type: "clawdio:worktree-worker", isolation: "worktree", prompt: "Implement issue #10 in <repo>.")
Agent(subagent_type: "clawdio:worktree-worker", isolation: "worktree", prompt: "Implement issue #11 in <repo>.")
Agent(subagent_type: "clawdio:worktree-worker", isolation: "worktree", prompt: "Implement issue #12 in <repo>.")
```

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

Via `AskUserQuestion`:
- "Review all PRs" → invoke Skill(clawdio:review-coordination) on each successful PR
- "Review PR #N" → review a specific one
- "Done for now" → stop

For any blocked results, report the reason and offer to retry or skip.
