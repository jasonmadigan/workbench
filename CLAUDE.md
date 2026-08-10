# clawdio

Claude Code development instructions for a portable Claude Code and Codex SDLC plugin.

## Architecture

`agents/router.md` is the canonical routing policy. Claude Code discovers it as a native agent; Codex reaches the same file through `skills/router/SKILL.md`. Shared skills provide workflow knowledge, and hooks enforce edit-time guardrails through one portable implementation.

```
you -> router -> specialist subagent(s) -> result
                    |
                    +-- skills (router adapter, next, ship, pluck, pr-description, issues, doc-sync, review-coordination, verify-findings, merge-gate, worktree-recovery, parallel-ship)
                    +-- hooks (block secrets, doc-sync-reminder, lint, format)
```

**Critical Claude dispatch rule:** never pass `name` to the Agent tool. Full cross-client dispatch and external-skill resolution rules live in `references/dispatch-rules.md`.

## Structure

```
agents/          subagent definitions (.md)
skills/          on-demand skills (skills/*/SKILL.md)
hooks/           lifecycle hooks (shared config and Python implementation)
references/      supporting docs agents can read
docs/            docs/architecture.md, docs/contributing.md, docs/references.md
.claude-plugin/  Claude manifest and shared marketplace
.codex-plugin/   Codex manifest
AGENTS.md        Codex repository instructions
```

## Key files

| File | Purpose |
|-|-|
| `agents/router.md` | entry point -- classifies tasks, dispatches to specialist agents |
| `skills/router/SKILL.md` | thin Codex entry adapter; loads the canonical router and dispatch rules |
| `agents/worktree-worker.md` | isolated implementation agent for shipping issues via worktrees |
| `skills/ship/SKILL.md` | full lifecycle skill: implement, push, PR, self-review, merge-prep |
| `skills/next/SKILL.md` | scans GitHub and Jira for actionable work, ranked by project boards where present |
| `skills/pluck/SKILL.md` | claim unassigned issues from the repo backlog |
| `skills/issues/SKILL.md` | GitHub issue lifecycle: create, update, link PRs, manage state |
| `skills/pr-description/SKILL.md` | PR body template and conventions |
| `skills/doc-sync/SKILL.md` | verifies and fixes docs against actual repo contents |
| `skills/review-coordination/SKILL.md` | coordinates multi-specialist PR review fanout |
| `skills/verify-findings/SKILL.md` | adversarial verification of specialist findings before presenting or posting |
| `skills/merge-gate/SKILL.md` | pre-merge safety checks |
| `skills/worktree-recovery/SKILL.md` | recovers in-progress worktree workers |
| `skills/parallel-ship/SKILL.md` | dispatches multiple worktree-workers for multi-issue ship |
| `hooks/hooks.json` | shared lifecycle hook registration |
| `hooks/file_hook.py` | normalises Claude and Codex edit payloads, then applies hook policy |
| `hooks/test_file_hook.py` | regression tests for both clients' edit payloads and path policy |
| `references/dispatch-rules.md` | cross-client agent dispatch, user interaction, and external capability resolution |
| `.claude-plugin/plugin.json` | Claude Code plugin manifest |
| `.codex-plugin/plugin.json` | Codex plugin manifest; name and version must match the Claude manifest |

## Keeping docs in sync

After changing files in `agents/`, `skills/`, `hooks/`, the portability rules, or either manifest, invoke `clawdio:doc-sync` before committing. It checks `README.md`, `AGENTS.md`, `CLAUDE.md`, the docs, component catalogues, hook registration, and manifest version parity.

## Conventions

- Agents in `agents/*.md`: as short as possible. Decision trees, anti-pattern tables, verification checklists where they earn their place.
- Skills in `skills/*/SKILL.md`: progressive disclosure. Lead with the rule, details below.
- Hook policy in `hooks/file_hook.py`: deterministic, fast, and silent when optional tools are missing. Keep `hooks/hooks.json` declarative.
- Keep client mechanics in `references/dispatch-rules.md`; never duplicate an agent prompt for Codex.
- Treat third-party skills as capability providers and maintain cross-client fallbacks centrally.
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

### PR review comments

- All findings go as **inline comments** on the specific diff lines. No exceptions.
- The review body contains the verdict line and focus table only. Never duplicate findings in the body.
- Nits are not posted unless the user explicitly asks for them.
- One sentence per finding. State the problem and the fix. Do not explain what the code does, how the language works, or why the fix is better. The reader is a competent engineer.
- No preamble on inline comments ("This line...", "Here we see..."). Start with the severity label and the problem.
- Bad: "**Important:** This function doesn't handle the case where the input slice is nil, which could cause a nil pointer dereference at runtime when the caller passes an uninitialised variable. Consider adding a nil check before the loop."
- Good: "**Important:** nil slice causes panic. Guard before the loop."

## Dependencies

- [agent-skills](https://github.com/addyosmani/agent-skills) -- declared Claude dependency for security, code review, TDD, debugging, and git workflow
- [dev-team-plugin](https://github.com/kuadrant/dev-team-plugin) -- declared Claude dependency for `kdt:*` feature-design and lifecycle workflows; cross-client fallback compositions are in the dispatch rules
- [edge-tooling](https://github.com/openshift-eng/edge-tooling) marketplace -- installed plugins: `challenge` (adversarial hypothesis review), `git-commits` (small-commits structuring), `pr-review` (yolo-agent, vet-review, coderabbit triage), `github` (pr-queue), `skills-review` (skill linting), `threat-model`, `edge-scrum`
- `gh` CLI (authenticated) -- verify with `gh auth status`
- GitHub MCP server -- provides `mcp__github__*` tools for issue/PR comment threads
- [Atlassian MCP](https://github.com/sooperset/mcp-atlassian) -- provides `mcp__atlassian__jira_*` tools for Jira integration (optional)

## Docs

- [docs/architecture.md](docs/architecture.md) -- design rationale and decisions
- [docs/contributing.md](docs/contributing.md) -- how to write agents, skills, hooks
- [docs/references.md](docs/references.md) -- Claude Code and Codex primitives and execution surfaces
