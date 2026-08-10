---
name: next
description: Scans GitHub and Jira for actionable work, ranked by the repo's GitHub Projects (v2) board, or a saved team view of it, when one exists. Shows board-prioritised issues, issues assigned to you, PRs needing review, your open PRs and their status, and open Jira tickets. Use when the user asks "what's on?", "what should I work on?", "what next?", or "next project issues?".
---

# Next

Scan GitHub and Jira to find actionable work. Invoke via `clawdio:next`.

Where the repo's issues sit on an active GitHub Projects (v2) board, the board is the primary prioritisation signal: it carries deliberate sprint, priority, and status decisions. The raw issue/PR backlog is the fallback when no board exists.

## Step 1: Query GitHub

Detect the repo with `gh repo view`, then run all three queries:

```bash
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')

gh search issues --assignee=@me --state=open --repo="$REPO" --json number,title,labels,updatedAt,url --limit 20

# if the above returns zero results, query the backlog
gh search issues --no-assignee --state=open --repo="$REPO" --json number,title,labels,updatedAt,url --limit 10 --sort updated

gh search prs --review-requested=@me --state=open --repo="$REPO" --json number,title,author,updatedAt,url --limit 20

gh pr list --author @me --json number,title,updatedAt,url,reviewDecision --limit 20
```

For "what's on everywhere" or "across all repos", drop `--repo` from the commands above and replace `gh pr list` with `gh search prs --author=@me --state=open`.

## Step 2: Project boards

Discover the board through the open issues' `projectItems`, not `repository.projectsV2` alone; the repo-level project list can be stale. In all-repos mode, run discovery per repo in scope.

For a Kuadrant repository or team view, read `references/kuadrant.md` for its board fields, saved-view, and Jira conventions.

Project queries need the `project` (or `read:project`) token scope. If the GraphQL call fails with a scope error, say so in one line and fall back to the raw backlog rather than failing the scan.

### Discover boards

```bash
gh api graphql -f query='
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    issues(first: 50, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number title updatedAt
        assignees(first: 5) { nodes { login } }
        projectItems(first: 3) {
          nodes {
            project {
              number title closed
              owner { ... on Organization { login } ... on User { login } }
            }
          }
        }
      }
    }
  }
}' -f owner="${REPO%/*}" -f repo="${REPO#*/}"
```

Dedupe the projects across all issues and exclude any with `closed: true`. If no open project remains, skip the rest of this step silently: the raw backlog behaviour from step 1 stands and the output makes no mention of boards.

### Saved team views

Teams often work from a filtered view of the board, not the raw item list. When the user references a view (an `/orgs/<org>/projects/<n>/views/<m>` URL, or a phrase like "the team view"), reproduce that view. The per-issue scan below structurally cannot: views filter on board fields and aggregate items across repos.

The view's filter string is exposed via GraphQL:

```bash
gh api graphql -f query='
query {
  organization(login: "<org>") {
    projectV2(number: <board>) {
      view(number: <view>) { name filter layout }
    }
  }
}'
```

Parse the filter tokens: `field:"value"` is single-select equality, `sprint:@current` is the iteration whose start date plus duration spans today, a leading `-` negates, bare words match title text. Then page the board items and filter client-side, requesting `fieldValueByName` for every field named in the filter plus Status and Sprint:

```bash
gh api graphql --paginate -f query='
query($endCursor: String) {
  organization(login: "<org>") {
    projectV2(number: <board>) {
      items(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          type
          status: fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
          sprint: fieldValueByName(name: "Sprint") { ... on ProjectV2ItemFieldIterationValue { title startDate duration } }
          content {
            ... on Issue { number title state repository { name } assignees(first: 5) { nodes { login } } }
            ... on PullRequest { number title state repository { name } }
            ... on DraftIssue { title }
          }
        }
      }
    }
  }
}'
```

Items-side paging is the point here: a view can be cross-repo, so walking one repo's issues cannot reproduce it. A few hundred items paginate fine; this path is only taken when a view is in play.

Rank view items by Status column order, assigned-to-me or unassigned first within each column. Surface open items only: board views usually show a Done column, never list it. When a view drove the selection, head the board section with the view and skip the per-issue scan.

### Discover fields

Field names vary per board. Do not assume them:

```bash
gh project field-list <number> --owner <project-owner> --format json
```

Identify:

- the status single-select (name matching Status; note the option order, the first column, e.g. Todo, is the "up next" state)
- a priority single-select (Priority or similar; note the option order, e.g. MoSCoW Must > Should > Could)
- an iteration field (Sprint) if present

Tolerate missing fields and rank with whatever the board provides.

### Fetch item field values

Query per-issue, not per-board. Org boards can hold hundreds of cross-repo items, so `issues -> projectItems -> fieldValueByName` scales with the repo while dumping the whole board does not. Extend the discovery query's `projectItems` selection with:

```graphql
projectItems(first: 3) {
  nodes {
    project { number }
    status: fieldValueByName(name: "Status") {
      ... on ProjectV2ItemFieldSingleSelectValue { name }
    }
    priority: fieldValueByName(name: "Priority") {
      ... on ProjectV2ItemFieldSingleSelectValue { name }
    }
    sprint: fieldValueByName(name: "Sprint") {
      ... on ProjectV2ItemFieldIterationValue { title startDate duration }
    }
  }
}
```

Substitute the discovered field names into `fieldValueByName`.

### Rank

1. Current-sprint items first: the iteration whose `startDate` plus `duration` (days) spans today. Non-sprint items after.
2. Within each: status Todo (or the board's first column), assigned to me or unassigned, ordered by the priority field's option order (Must > Should > Could > unset).
3. In Progress items assigned to me are not new work. Surface them separately as already in flight, a WIP reminder.
4. Ready For Review / In Review items where I am reviewer or author fold into the PR sections in step 6. Do not duplicate them in the board section.
5. Done items and items on closed projects never appear.

## Step 3: Check component ownership

Check if the repo has a Kubernetes-style `OWNERS` file at the repo root:

```bash
gh api "repos/$REPO/contents/OWNERS" --jq '.content' 2>/dev/null | base64 -d
```

If `OWNERS` exists, parse the YAML for `approvers` and `reviewers` lists. Get the current user's GitHub handle:

```bash
gh api user --jq '.login'
```

If the user appears in either list, they are a component owner for this repo. Query for open PRs and issues that are **not** already assigned to or requesting review from the user (those are already captured in step 1):

```bash
gh search prs --repo="$REPO" --state=open --json number,title,author,updatedAt,url,labels --limit 20

gh search issues --repo="$REPO" --state=open --no-assignee --json number,title,labels,updatedAt,url --limit 20
```

Filter out any results already shown in step 1 (same PR/issue number). These go into a **Component owner** section in the output.

If there is no `OWNERS` file, or the user is not listed, skip this step silently.

## Step 4: Repo activity

Regardless of `OWNERS`, check for open PRs in the repo that need attention. These are PRs not authored by the user that have no reviews yet:

```bash
gh pr list --state open --json number,title,author,updatedAt,url,reviewDecision,reviewRequests --limit 20
```

Filter the `gh pr list` output to PRs where:
- `author.login` is not the current user (compare against `gh api user --jq '.login'`)
- `reviewDecision` is empty or `REVIEW_REQUIRED` (no reviews submitted yet)

Exclude any PRs already captured in step 1 or step 3.

These go into a **Repo activity** section. This catches PRs on small teams where explicit review requests aren't always used.

If no unreviewed PRs from others exist, skip this section silently.

## Step 5: Query Jira

If the Atlassian MCP server is available (check for `mcp__atlassian__jira_search`), run two queries:

**Assigned to me:**
```
mcp__atlassian__jira_search with JQL: assignee = currentUser() AND status != Done ORDER BY updated DESC
```

**Contributor (custom field):**
```
mcp__atlassian__jira_search with JQL: cf[10466] = currentUser() AND status != Done ORDER BY updated DESC
```

Merge and deduplicate results by issue key (an issue can appear in both queries). Mark contributor-only issues with "(contributor)" so the user can distinguish ownership from involvement.

Show open Jira tickets under their own section with key, summary, status, priority, and project.

If `mcp__atlassian__jira_search` is not available, skip this step silently.

For a repository-specific Jira mapping, load its conditional reference. Without one, show all Jira tickets without org filtering.

## Step 6: Format output

Present results in markdown tables. Group by priority (highest first):

1. **Board** -- only when step 2 found an open board. Head the section with the board and, when applicable, the saved view and filter so the applied lens is visible. List ranked items with status, priority, and sprint annotations, then already-in-flight items beneath as a WIP reminder.
2. **Address feedback** -- my PRs where `reviewDecision` is `CHANGES_REQUESTED`. Invoke `clawdio:ship --resume` to fix.
3. **Review** -- PRs requesting my review. Open with `gh pr view <number>`.
4. **Merge** -- my PRs where `reviewDecision` is `APPROVED`. Merge with `gh pr merge <number> --squash`.
5. **My PRs** -- my open PRs where `reviewDecision` is `REVIEW_REQUIRED`
6. **Implement** -- GitHub issues assigned to me. Invoke `clawdio:ship #<number>` to start. Where an issue is a board item, annotate its status and priority inline from the step 2 data; no extra calls.
7. **Backlog** -- unassigned issues in this repo. Only shown when no issues are assigned to me. Invoke `clawdio:ship #<number>` to pick up, or `clawdio:pluck` to claim without implementing.
8. **Component owner** -- open PRs and unassigned issues in repos where I am an `OWNERS` approver/reviewer
9. **Repo activity** -- open PRs from others with no reviews yet
10. **Jira** -- open Jira tickets assigned to me

Skip sections with no results. Omit empty tables entirely. When no open board exists, the output has no board section, no annotations, and no mention of boards.

Every table uses three columns. Build the first column as a markdown link from the `url` field returned by `gh`. Example row: `| [#30](https://github.com/org/repo/issues/30) | Title here | detail |`

For Jira tickets, build the link from the issue key: `| [PROJ-123](https://site.atlassian.net/browse/PROJ-123) | Title | status, priority |`

## Step 7: Recommend next action

Suggest what to tackle first. When a board exists, the top-ranked board item is the default suggestion. Offer to invoke `clawdio:ship` on the top item or open it with `gh issue view <number>` / `gh pr view <number>`.
