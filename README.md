# clawdio

Claude Code plugin for SDLC automation. A router agent dispatches to specialist subagents based on the task. Skills provide cross-cutting workflow knowledge. Hooks enforce guardrails.

The premise: the bottleneck is never orchestration infrastructure -- it's agent reliability. This plugin invests in good agents, skills, and hooks that work natively in Claude Code, replacing a [custom Go orchestrator](https://github.com/jasonmadigan/clawdio) that was over-built for what it did.

## Install

```bash
# add the marketplace
claude plugin marketplace add jasonmadigan/clawdio

# install the plugin (user scope, available in all repos)
claude plugin install clawdio
```

For local development:

```bash
claude --plugin-dir /path/to/clawdio

# or with a specific agent and permissions
claude --plugin-dir ~/Work/clawdio --dangerously-skip-permissions --agent clawdio:router
```

Reload after changes without restarting Claude:

```
/reload-plugins
```

## Dependencies

Install these separately -- clawdio agents and skills reference them.

### Plugins

| Plugin | Install | What it provides |
|-|-|-|
| [agent-skills](https://github.com/addyosmani/agent-skills) | `claude plugin marketplace add addyosmani/agent-skills && claude plugin install agent-skills` | Security hardening, code review, TDD, debugging, git workflow, spec-driven development |
| [dev-team-plugin](https://github.com/kuadrant/dev-team-plugin) | `claude plugin marketplace add kuadrant/dev-team-plugin && claude plugin install kdt` | Design docs, feature lifecycle, Go PR review, doc verification, external contribs |
| [playwright](https://github.com/anthropics/claude-plugins-official) | `claude plugin install playwright` | Browser automation for UI test verification |

Clawdio handles SDLC orchestration (router, specialists, shipping). agent-skills handles cross-cutting development practices. kdt provides design doc workflows and feature lifecycle management. The router dispatches to all three.

### CLI tools

| Tool | Purpose | Used by |
|-|-|-|
| [`gh`](https://cli.github.com/) | GitHub issue/PR operations | implement, review, triage, refine, address-feedback, next, ship, worktree-worker, issues |

Must be authenticated (`gh auth login`).

### MCP servers

| Server | Purpose | Used by |
|-|-|-|
| GitHub MCP | Issue/PR comments, review threads | address-feedback |
| [Atlassian MCP](https://github.com/sooperset/mcp-atlassian) | Jira issue search, creation, updates | next, triage, router |

Install Atlassian MCP via `claude mcp add atlassian -s user -e JIRA_URL=https://your-site.atlassian.net -e JIRA_USERNAME=you@company.com -e JIRA_API_TOKEN=your-token -- uvx mcp-atlassian --jira-url https://your-site.atlassian.net`. Requires `uv` installed.

## How it works

Talk to the **router** agent. It classifies your request and dispatches the right specialist.

```mermaid
graph LR
    You -->|request| Router
    Router -->|classify & dispatch| Agents[agents: implement, triage, refine, address-feedback, release-notes, test-writer, docs, worktree-worker]
    Router -->|invoke| Skills[skills: next, ship, pluck, issues, pr-description, doc-sync, review-coordination, verify-findings, merge-gate, worktree-recovery, parallel-ship]
    Router -->|review fanout| Review[code-reviewer + test-verifier + domain specialists]
    Agents -->|result| Router
    Review -->|findings| Router
    Router -->|present & confirm| You
    Hooks -.->|guardrails| Agents
```

### Review flow

The router owns the review fanout. Subagents can't spawn sub-subagents, so the router dispatches all specialists in parallel.

```mermaid
graph TD
    A[User: review PR] --> B[Router: classify files]
    B --> BB[classifier agent: bucket changed files by behaviour vs mechanical]
    BB --> C{File types?}
    C -->|always| D[code-reviewer]
    C -->|always| E[test-verifier]
    C -->|*.go| F[go-k8s-reviewer]
    C -->|*auth*| G[auth-reviewer]
    C -->|*crypto*| H[security-auditor]
    D & E & F & G & H -->|findings| I[Router: merge across axes]
    I --> V[verify-findings: one verifier per Critical/Important finding]
    V -->|confirmed + plausible| J{Verdict}
    V -->|refuted| VF[filtered out, shown collapsed]
    J -->|APPROVE| K[offer merge]
    J -->|CHANGES REQUESTED| L[draft PR comment]
    J -->|BLOCKED| L
    L --> M{User: post?}
    M -->|post| N[gh pr comment]
    M -->|edit| L
    M -->|don't post| O{Next?}
    N --> O
    K --> O
    O -->|address feedback| P[address-feedback agent]
    O -->|merge| Q[merge gate]
    O -->|done| R[next]
    P --> S{Next?}
    S -->|re-review| B
    S -->|merge| Q
    S -->|next| R
```

### Ship flow

Full lifecycle from issue to merged PR. Supports `--resume` (pick up mid-flow), `--skip-review`, and `--draft`.

```mermaid
graph TD
    A[User: ship #N] --> AA{resume?}
    AA -->|existing state| AB[resume from saved phase]
    AA -->|fresh| B[assign issue + in-progress label]
    AB --> B
    B --> C[implement agent]
    C --> D{diff gate}
    D -->|no changes| E[blocked: comment on issue, remove label]
    D -->|changes exist| F[pre-ship checks]
    F --> G[self-review locally]
    G --> H{findings?}
    H -->|critical/important| I[fix + recommit]
    I --> G
    H -->|clean| J[push + gh pr create --draft]
    J --> K{CI checks}
    K -->|pass| L{repo type?}
    K -->|fail| N[report failures, offer to fix]
    K -->|running| O[report status, check back later]
    N --> I
    L -->|personal + user says merge| P[gh pr merge --squash]
    L -->|team| Q[report draft PR link]
```

For multiple issues ("ship #1, #2, #3"), the router dispatches worktree-worker agents in parallel, each in an isolated git worktree.

### What's on flow

Scoped to the current repo by default. Checks OWNERS files for component ownership.

```mermaid
graph TD
    A[User: what's on] --> B[detect repo]
    B --> C[query issues + PRs assigned/requesting review]
    B --> D[check OWNERS file]
    D -->|user is owner| E[query unassigned issues + open PRs]
    D -->|not owner| F[skip]
    B --> G[query Jira if available]
    C & E & F & G --> H{group by priority}
    H --> I[address feedback]
    H --> J[review requested]
    H --> K[merge ready]
    H --> L[my PRs awaiting review]
    H --> M[implement]
    H --> N[component owner]
    H --> O[Jira]
    I & J & K & L & M & N & O --> P[present prioritised table]
    P --> Q[suggest top action]
```

### Typical commands

**"Pluck"** -- invokes the `pluck` skill. Shows unassigned issues in the current repo. Pick ones to claim without starting implementation.

**"What's on?"** -- invokes the `next` skill. Queries GitHub for issues, PRs, and feedback in the current repo, ranked by the project board (or a saved team view of it) when one exists. Returns a prioritised table.

**"Ship #42"** -- invokes the `ship` skill. Implements, pushes, creates PR, self-reviews, fixes findings, reports back.

**"Review this PR"** -- classifies files, dispatches specialist reviewers in parallel, collects findings, drafts PR comment.

**"Triage this issue"** -- dispatches the triage agent. Assesses readiness, recommends workflow (implement, refine, split, or human review).

**"This issue is vague"** -- dispatches the refine agent. Produces a structured spec with testable acceptance criteria.

**"Ship #1, #2, #3"** -- dispatches worktree-worker agents in parallel, each in its own worktree. Collects results and presents a summary table.

**"Create an issue"** -- invokes the `issues` skill. Creates issues with acceptance criteria, manages state, links PRs.

## Agents

| Agent | Purpose |
|-|-|
| router | Task intake, classification, delegation. Coordinates review fanout. Never writes code. |
| implement | Takes a well-defined issue, writes code, runs tests, commits |
| code-reviewer | General code quality: correctness, readability, architecture, naming |
| security-auditor | Security review: injection, auth bypasses, secrets, crypto, OWASP |
| go-k8s-reviewer | Go idioms, concurrency, controller patterns, CRD conventions, RBAC |
| auth-reviewer | OAuth2/OIDC flows, token handling, policy evaluation, standards compliance |
| triage | Assesses issue readiness, labels, prioritises, recommends workflow |
| refine | Turns vague issues into implementable specs with acceptance criteria |
| address-feedback | Reads PR review comments, categorises, fixes, reports what needs human input |
| release-notes | Generates grouped release notes between git tags |
| test-writer | Finds coverage gaps, writes targeted tests matching project patterns |
| test-verifier | Verifies PR test plans: runs tests, checks criteria, drives browser for UI checks |
| verifier | Adversarial verifier for exactly one finding: refutes or confirms with evidence |
| docs | Writes and updates documentation. Verifies every example and path. |
| worktree-worker | Self-contained implement-to-PR in an isolated worktree. For parallel multi-issue dispatch. |

## Skills

Clawdio provides its own skills for SDLC orchestration. For cross-cutting development practices (TDD, debugging, security hardening, code review), it leans on the companion [agent-skills](https://github.com/addyosmani/agent-skills) plugin. Design doc workflows and feature lifecycle come from [dev-team-plugin](https://github.com/kuadrant/dev-team-plugin) (kdt).

### Clawdio skills

| Skill | Trigger | Args | Purpose |
|-|-|-|-|
| next | "what's on?", "what next?", "next project issues?" | none | Scans GitHub and Jira for issues, PRs, and feedback across repos, ranked by project boards or saved team views where present |
| ship | "ship #42" | `<issue>`, `--resume`, `--skip-review`, `--ready` | Full lifecycle: implement > push > draft PR > self-review > fix |
| pluck | "pluck", "claim issue", "grab issue" | none | Claim unassigned issues from the repo backlog without implementing |
| pr-description | Creating a PR | none | PR body template: summary, linked issue, test evidence |
| issues | "create issue", "update issue" | `create`, `update`, `close`, `link`, `--repo` | Create, update, close issues. Manages PR-issue links and lifecycle state. |
| doc-sync | "check docs", "are docs up to date" | none | Verify and fix documentation accuracy against actual repo contents |
| review-coordination | PR review dispatch | none | Coordinates multi-specialist PR review fanout |
| verify-findings | "verify", "double-check", after findings return | none | Adversarial verification of Critical/Important findings before presenting or posting |
| merge-gate | pre-merge checks | none | Pre-merge safety checks before any merge |
| worktree-recovery | worktree recovery | none | Recovers in-progress worktree workers before dispatching new ones |
| parallel-ship | "ship #1, #2, #3" | `<issues>` | Dispatches multiple worktree-workers in parallel for multi-issue ship |

### agent-skills (companion plugin)

Clawdio agents invoke [agent-skills](https://github.com/addyosmani/agent-skills) skills at key workflow points. These provide the development discipline that clawdio orchestrates.

| agent-skills skill | Used by | When |
|-|-|-|
| code-review-and-quality | code-reviewer, go-k8s-reviewer | Five-axis review (correctness, readability, architecture, security, performance) |
| code-simplification | code-reviewer | Identify simplification opportunities in reviewed code |
| security-and-hardening | security-auditor, auth-reviewer | OWASP, secrets, auth/authz checks |
| test-driven-development | implement, worktree-worker, test-verifier, test-writer | RED-GREEN-REFACTOR loop |
| incremental-implementation | implement, worktree-worker, address-feedback | One logical change per commit, vertical slices |
| debugging-and-error-recovery | implement, worktree-worker, address-feedback | When tests fail and cause is unclear |
| spec-driven-development | implement, refine | Spec-first for non-trivial changes |
| planning-and-task-breakdown | refine, triage | Break scope into ordered tasks |
| api-and-interface-design | go-k8s-reviewer, auth-reviewer | API surface stability, Hyrum's Law checks |
| performance-optimization | go-k8s-reviewer | N+1 queries, unbounded ops, async patterns |
| git-workflow-and-versioning | ship, worktree-worker, address-feedback | Commit conventions, branch hygiene |
| shipping-and-launch | ship | Pre-ship checklist in phase 2 |
| documentation-and-adrs | docs | ADR structure and documentation patterns |
| browser-testing-with-devtools | test-verifier | Drive browser for UI verification |

### kdt (companion plugin)

The router dispatches [dev-team-plugin](https://github.com/kuadrant/dev-team-plugin) skills for design and feature lifecycle work.

| kdt skill | Trigger | Purpose |
|-|-|-|
| feature-design | "design doc", "feature design" | Create and review design docs, generate issues from TODOs |
| feature-implement | "pick up", "implement from design" | Pick up issues from design docs, manage feature lifecycle |
| pr-closes-issue | "does the PR close the issue" | Verify PR changes match issue requirements |
| external-contribs | "external contribs", "community PRs" | Find external contributions needing attention |

## Hooks

| Hook | Trigger | Purpose |
|-|-|-|
| block-env-writes | Before Write/Edit | Blocks writes to `.env`, credentials, `.pem`, `.key` files |
| doc-sync-reminder | After Write/Edit | Reminds to update docs when agent/skill/hook files change |
| format-on-save | After Write/Edit | Runs project formatter if configured (prettier, gofmt, clang-format) |
| lint-on-edit | After Write/Edit | Runs project linter if configured (eslint, golangci-lint) |

## Structure

```
agents/           subagent definitions (one .md per agent)
skills/           on-demand skills (SKILL.md per directory)
hooks/            lifecycle hooks (hooks.json)
references/       supporting docs agents can read
docs/             architecture decisions and project context
.claude-plugin/   plugin manifest and marketplace config
```

## Personalisation

The go-k8s-reviewer and auth-reviewer ship with generic definitions suitable for any Go/K8s or auth project. For domain-specific review depth, override them with personal versions in `~/.claude/agents/` -- personal agents take precedence over plugin agents.

Personal agent overrides stay out of this repo. They're your competitive advantage, not a shared concern.

## Development

See [docs/contributing.md](docs/contributing.md) for how to write agents, skills, and hooks.

Edit, test locally with `claude --plugin-dir .`, push, then `claude plugin update clawdio@jasonmadigan-clawdio`.

## Design

See [docs/architecture.md](docs/architecture.md) for the full design rationale, including why this is a plugin and not an orchestrator, the three-tier primitive location model, and future Agent SDK migration path.

See [docs/grill-findings.md](docs/grill-findings.md) for the structured interview that informed these decisions.
