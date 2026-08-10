---
name: worktree-recovery
description: Recovers in-progress worktree workers. Use when the router is about to dispatch new worktree-workers.
---

# Worktree Recovery

Recovers in-progress worktree workers. Invoked by the router before dispatching new worktree-workers.

Read `../../references/dispatch-rules.md` before dispatching or asking the user
for a decision.

## Detection

Check for existing worktrees with state files. This catches workers that died mid-run.

```bash
git worktree list --porcelain | grep '^worktree ' | awk '{print $2}'
```

For each worktree path, check for `.clawdio-state`:

```bash
cat <worktree-path>/.clawdio-state 2>/dev/null
```

## User prompt

If state files exist, present them through the active client's user-decision mechanism:

```
Found in-progress worktree work:
- <worktree>: issue <ref>, phase: <phase>, last updated: <time>

Options: "Resume these", "Clean up and start fresh", "Leave them"
```

## Phase-to-action table

| Phase found | Resume action |
|-|-|
| understand | Re-dispatch worktree-worker on the same issue, same worktree |
| implement | Re-dispatch, code may be partially written |
| blocked | Report the error to the user, offer to retry or skip |
| pushed | Branch exists remotely, skip to PR creation |
| pr-created | PR exists, skip to review |
| complete | Nothing to do, clean up the worktree |

When resuming, pass the existing worktree path to the agent rather than creating a new one.
