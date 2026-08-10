# Kickoff

> Historical snapshot from 25 April 2026. See `README.md` and `docs/architecture.md` for the current Claude Code and Codex design.

At kickoff, this repo was a Claude Code plugin called **clawdio**. It replaced a custom Go orchestrator with native Claude Code primitives: agents, skills, hooks, and MCP configs.

## What we're building

A personal SDLC toolkit where I talk to a **router agent** and it handles everything. "What's on?" shows me priorities. "Ship #42" dispatches an implement agent, self-reviews, pushes, and creates a PR. "Review this PR" fans out to domain specialist reviewers in parallel.

The key insight: the bottleneck was never orchestration infrastructure -- it was agent reliability. Better agents beat better orchestration.

## Architecture

Router agent -> specialist subagents -> skills for cross-cutting knowledge -> hooks for guardrails.

Read `docs/architecture.md` for full context and `docs/grill-findings.md` for the structured interview that led to these decisions.

## What existed at kickoff

- 13 agent definitions in `agents/` (router, implement, code-reviewer, security-auditor, go-k8s-reviewer, auth-reviewer, test-verifier, triage, refine, address-feedback, release-notes, test-writer, docs)
- 3 skills in `skills/` (next, ship, pr-description)
- 3 hooks (block-env-writes, format-on-save, lint-on-edit)
- Plugin manifest + marketplace.json

## Initial next steps

1. **Test the router.** Install the plugin (`claude plugin marketplace add jasonmadigan/clawdio && claude plugin install clawdio`), invoke the router, see if the dispatch pattern works.
2. **Hone the agents.** The current definitions are first drafts. Run them on real tasks and iterate based on actual output quality.
3. **Override domain specialists.** The plugin ships generic go-k8s-reviewer and auth-reviewer. Override with domain-specific versions in `~/.claude/agents/`.
4. **Install agent-skills.** `claude plugin marketplace add addyosmani/agent-skills && claude plugin install agent-skills` for companion skills (TDD, debugging, security, code review, git workflow).
5. **Wire MCP.** GitHub MCP server config for issue/PR operations.

## Constraints

- Vertex AI only (no direct Anthropic API). Set `CLAUDE_CODE_USE_VERTEX=1` etc.
- British English. No emojis. Terse docs.
- Domain specialist agents (named after real people) stay in `~/.claude/agents/`, never in the public repo.
