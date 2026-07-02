# clawdio

Personal Claude Code plugin for SDLC automation.

## Architecture

`agents/router.md` classifies tasks and dispatches to specialist subagents. Skills provide cross-cutting knowledge invoked via the Skill tool. Hooks in `hooks/hooks.json` enforce guardrails at commit time.

```
you -> router -> specialist subagent(s) -> result
                    |
                    +-- skills (next, ship, pluck, pr-description, issues, doc-sync, review-coordination, verify-findings, merge-gate, worktree-recovery, parallel-ship)
                    +-- hooks (block secrets, doc-sync-reminder, lint, format)
```

**Critical dispatch rule:** NEVER pass `name` to the Agent tool. Named agents spawn into idle mailbox mode and never execute. Use `subagent_type` and track by returned `agentId`. See `docs/architecture.md` for details.

## Structure

```
agents/          subagent definitions (.md)
skills/          on-demand skills (skills/*/SKILL.md)
hooks/           lifecycle hooks (hooks/hooks.json)
references/      supporting docs agents can read
docs/            docs/architecture.md, docs/contributing.md, docs/references.md
.claude-plugin/  plugin manifest (.claude-plugin/plugin.json)
```

## Key files

| File | Purpose |
|-|-|
| `agents/router.md` | entry point -- classifies tasks, dispatches to specialist agents |
| `agents/worktree-worker.md` | isolated implementation agent for shipping issues via worktrees |
| `skills/ship/SKILL.md` | full lifecycle skill: implement, push, PR, self-review, merge-prep |
| `skills/next/SKILL.md` | scans GitHub and Jira for actionable work |
| `skills/pluck/SKILL.md` | claim unassigned issues from the repo backlog |
| `skills/issues/SKILL.md` | GitHub issue lifecycle: create, update, link PRs, manage state |
| `skills/pr-description/SKILL.md` | PR body template and conventions |
| `skills/doc-sync/SKILL.md` | verifies and fixes docs against actual repo contents |
| `skills/review-coordination/SKILL.md` | coordinates multi-specialist PR review fanout |
| `skills/verify-findings/SKILL.md` | adversarial verification of specialist findings before presenting or posting |
| `skills/merge-gate/SKILL.md` | pre-merge safety checks |
| `skills/worktree-recovery/SKILL.md` | recovers in-progress worktree workers |
| `skills/parallel-ship/SKILL.md` | dispatches multiple worktree-workers for multi-issue ship |
| `hooks/hooks.json` | lifecycle hooks: secret blocking, doc-sync reminders, lint, format |
| `.claude-plugin/plugin.json` | plugin manifest (name, version, entry points) |

## Keeping docs in sync

After changing files in `agents/`, `skills/`, or `hooks/`, invoke `clawdio:doc-sync` before running `git commit`. It reads `README.md`, `CLAUDE.md`, `docs/architecture.md`, and `docs/contributing.md`, cross-references against `ls agents/*.md`, `ls -d skills/*/`, and `hooks/hooks.json`, and fixes discrepancies.

## Conventions

- Agents in `agents/*.md`: as short as possible. Decision trees, anti-pattern tables, verification checklists where they earn their place.
- Skills in `skills/*/SKILL.md`: progressive disclosure. Lead with the rule, details below.
- Hooks in `hooks/hooks.json`: deterministic, fast, fail silently if tools missing.
- Run `uvx skillsaw lint` to verify skill quality before committing skill changes.
- British English in all user-facing text.
- No emojis. No AI-sounding prose.

## Comment style

All externally-visible comments (PR reviews, issue comments, state updates) follow this style. See `skills/pr-description/SKILL.md` for PR body conventions and `skills/issues/SKILL.md` for issue comment conventions:

- Terse. Say what needs saying, stop.
- No preamble ("Great work!", "This PR looks good overall..."). Start with the content.
- No sign-offs ("Let me know if you have questions!", "Happy to discuss further!").
- No bullet-point walls when a sentence will do.
- Lower case where natural. Not aggressively so, just not formal.
- Findings use severity labels (Critical/Important/Nit) and file:line references. No prose wrapping.
- State changes are one line: "blocked: implement agent produced no changes." Not a paragraph.
- If there's nothing to say, don't comment. Silence is fine.
- PR review findings go as line-level comments on the specific code, not as a single wall of text. The verdict summary goes in the review body. Individual findings go on the lines they reference.

## Dependencies

- [agent-skills](https://github.com/addyosmani/agent-skills) plugin -- invoke via `agent-skills:<skill>` for security, code review, TDD, debugging, git workflow
- [dev-team-plugin](https://github.com/kuadrant/dev-team-plugin) plugin -- invoke via `kdt:<skill>` for design docs, feature lifecycle, Go PR review
- `gh` CLI (authenticated) -- verify with `gh auth status`
- GitHub MCP server -- provides `mcp__github__*` tools for issue/PR comment threads
- [Atlassian MCP](https://github.com/sooperset/mcp-atlassian) -- provides `mcp__atlassian__jira_*` tools for Jira integration (optional)

## Docs

- [docs/architecture.md](docs/architecture.md) -- design rationale and decisions
- [docs/contributing.md](docs/contributing.md) -- how to write agents, skills, hooks
- [docs/references.md](docs/references.md) -- Claude Code primitives and execution surfaces
