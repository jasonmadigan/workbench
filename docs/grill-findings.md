# Grill session findings

Structured interview conducted 2026-04-25 to understand actual workflows before designing the agent architecture.

> This records the original decision context. Clawdio now supports both Claude Code and Codex; see `docs/architecture.md` for the current portability design.

## Key findings

### Work patterns

- 3-5 repos in active rotation
- Equal split across feature implementation, PR review, and bug investigation
- Deliberate implementation process: read > refine > plan > code > self-review > PR > team review > feedback > merge
- AI assists across multiple steps, not just coding
- Works serially in practice despite building parallelism tooling

### Why parallel agents haven't worked

The bottleneck was never orchestration infrastructure -- it was that the agents themselves weren't reliable enough to run unsupervised. Skills, tools, and guardrails weren't in place to trust them. Failure modes were unpredictable: permissions issues, code that doesn't build, misunderstood scope, wrong patterns. The fix is better agents, not better orchestration.

### Review workflow (detailed)

1. Read the diff in GitHub
2. Open multiple specialist agents for first pass (e.g. Go specialist, auth specialist)
3. Read Coderabbit comments as another perspective
4. Validate agent findings against the actual code (are the issues real?)
5. Ask agent for summary of confirmed findings
6. Post review in own voice and style
7. Loop until PR is in good shape

This is already multi-agent and works well. The gap is in making it smoother, not fundamentally different.

### What would save the most time

Implementation of well-defined issues. This is the hardest to get right but the highest leverage.

### Issue readiness depends on codebase familiarity

In repos the agent knows well (good CLAUDE.md, agent has seen the patterns), less detail needed in the issue. In unfamiliar repos, more specification required. All active repos have reasonably good CLAUDE.md files already.

### Team context

- Team is actively adopting AI workflows
- Personal repos: full autonomy acceptable
- Team repos: agents assist, human stays in loop
- Org-level sharing (future): shared plugin that everyone installs

### Beyond SDLC

Significant time goes to:
- Release and downstream tracking (RHCL/OCP version mapping, what shipped where)
- Documentation and spec writing
- Operational/infrastructure work (CI/CD, test infra, dev env)
- All of these are candidates for agents/skills

### Trigger model

Not event-driven (webhooks/GHA) for personal work. The model is conversational: open Claude, ask "what's on?", get prioritised list, tell it to go. The router agent IS the interface. The pipeline view is a conversation, not a TUI.

### The clawdio verdict

Clawdio's value was the promise of parallel agent management. In practice:
- Skills, workflows, and prompt engineering belong in Claude Code primitives (portable, team can use them)
- Workflow chaining is better expressed as a router agent than hardcoded YAML transitions
- GitHub polling can be a skill (next) rather than a daemon
- Worktree management is built into Claude Code
- The TUI is replaced by the conversation itself

### Architecture chosen

Router agent + specialist subagents + skills + hooks + MCP. Start with Claude Code, port to Agent SDK when ceiling is hit (scheduling, GHA, custom UIs).

## Open questions from the grill

- How to handle the "org-level plugin" layer (shared across the team)?
- Which agent-skills from addyosmani/agent-skills to adopt vs build custom?
- How to handle Vertex quotas when running multiple parallel agents?
- Where does the release tracking workflow (RHCL/OCP) live -- plugin skill or separate tooling?
- How to handle multi-repo context (agent working on an issue that spans two repos)?
