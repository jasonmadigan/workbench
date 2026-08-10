---
name: pluck
description: Claim unassigned issues from the repo backlog. Shows an interactive picker, assigns selected issues to you. Use when you want to claim work without starting implementation, or to batch-claim at standup.
---

# Pluck

Claim unassigned issues from the current repo without implementing them. Invoke via `clawdio:pluck`.

Read the user-decision rules in `../../references/dispatch-rules.md` before
presenting the picker.

## Process

### Step 1: Detect context

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
USER=$(gh api user --jq '.login')
```

### Step 2: Query unassigned issues

```bash
gh search issues --no-assignee --state=open --repo="$REPO" --json number,title,labels,updatedAt,url --limit 10 --sort updated
```

If zero results: report "No unassigned issues in this repo." Stop.

### Step 3: Present picker

Show results as a numbered list. Each item:

```
1. #42 - Add retry logic to gateway client (bug, priority/high) - updated 3 days ago
2. #38 - Document rate limit headers (docs) - updated 1 week ago
3. #35 - Support custom TLS certificates - updated 2 weeks ago
```

Labels in parentheses after the title. Omit parentheses if no labels. Show relative time for last updated.

### Step 4: Multi-select

Ask the user to pick issues through the active client. Use multi-select when the client exposes it; otherwise accept comma-separated issue numbers. Options are the numbered items from step 3.

### Step 5: Assign

For each selected issue:

```bash
gh issue edit <number> --add-assignee "@me"
```

### Step 6: Confirm

Report what was claimed:

```
Claimed 2 issues:
- #42 Add retry logic to gateway client
- #38 Document rate limit headers

Next: `clawdio:ship #42` to start implementing, or `clawdio:next` to see the updated board.
```

Adjust the ship suggestion to reference the first claimed issue.
