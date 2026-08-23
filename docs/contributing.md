# Contributing

How to add agents, skills, and hooks without splitting the Claude Code and Codex implementations.

## Development workflow

1. Edit the canonical agent, skill, or hook implementation.
2. If client mechanics changed, update `references/dispatch-rules.md`; do not copy workflow text into an adapter.
3. Bump the version in both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`.
4. Run the validation suite below.
5. Smoke-test the router in both clients before publishing.

```bash
claude plugin validate --strict .
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
python3 -m py_compile hooks/file_hook.py
python3 -m unittest hooks/test_file_hook.py
uvx skillsaw lint

# Claude Code smoke test
claude --plugin-dir /path/to/clawdio --agent clawdio:router

# Codex smoke test through the local marketplace
codex plugin marketplace add /path/to/clawdio
codex plugin add clawdio@jasonmadigan-clawdio
```

Use the `plugin-creator` validator bundled with Codex; resolve its installed path locally rather than committing a machine-specific path. Claude Code can reload an active development session with `/reload-plugins`.

## Portability and reuse

There are four sources of truth:

- `agents/*.md` for specialist behaviour
- `skills/*/SKILL.md` for shared workflows
- `references/dispatch-rules.md` for client adaptation and external capability resolution
- `hooks/file_hook.py` for file-hook behaviour

The manifests, `skills/router/SKILL.md`, and `hooks/hooks.json` must remain thin. Never paste an agent body into a Codex custom-agent TOML file or duplicate hook shell snippets per client.

Third-party skill names express intent. Add their portable resolution and fallback once in `references/dispatch-rules.md`; do not vendor their instructions. A canonical agent must contain a usable baseline process so a provider can improve the workflow without making one client's package format a runtime requirement everywhere.

## Writing agents

Agents are canonical Markdown prompts in `agents/`, one file per agent. Claude Code discovers them directly. The Codex router supplies their resolved paths to built-in subagents.

### Format

```markdown
---
name: agent-name
description: One sentence. What it does and when to use it.
---

# Agent Name

One sentence role statement.

## Process

Numbered steps or gated phases. Use decision trees for classification logic.

## Anti-patterns

Table of common mistakes and their fixes.

## Rules

Hard constraints the agent must follow.
```

### Patterns to use

**Gated phases** for multi-step workflows. Group steps into phases with verification checklists between them:

```markdown
### Phase 1: Understand
1. Read the issue...

### Phase 2: Plan
2. State your approach...

- [ ] Approach covers all acceptance criteria
- [ ] No scope beyond what the issue asks
```

**Decision trees** for classification and triage logic. Use ASCII trees:

```
Input
├── Condition A?
│   └── Action A
├── Condition B?
│   └── Action B
└── Neither?
    └── Ask the user
```

**Anti-pattern tables** for common mistakes. Two columns: Problem and Fix:

```markdown
| Problem | Fix |
|-|-|
| Doing X without checking Y | Always check Y first |
```

**Severity labels** for review agents. Use consistent labels across all reviewers:

| Label | Meaning | Action |
|-|-|-|
| Critical | Blocks merge | Must fix |
| Important | Should be addressed | Should fix |
| Nit | Minor, optional | Author's call |

**Verification checklists** mid-process, not just at the end. Use markdown checkboxes:

```markdown
- [ ] All tests pass
- [ ] No unrelated changes
```

**Cross-skill capability references** where an optional provider improves the baseline:

```markdown
Resolve the `agent-skills:test-driven-development` capability for TDD.
```

### Conventions

- As short as possible, ideally. Every line should earn its place.
- Process steps should be concrete actions, not vague guidance.
- Rules should be things the agent would otherwise get wrong.
- The description field informs Claude dispatch and documents Codex routing intent. Make it precise.
- British English. No emojis. No AI-sounding prose.
- Any agent that posts externally-visible comments (PR reviews, issue updates) must follow the comment style in CLAUDE.md. Keep review severity and file:line evidence internally; make posted comments terse, friendly, concrete, and actionable.

### Worktree-isolated agents

Write-heavy agents run in an isolated git worktree when concurrent. Claude Code may provide isolation on dispatch; Codex workflows must create a separate worktree, pass its absolute path to the worker, verify the worker's repository root, or run serially. Conventions:

- The agent must not `cd` outside its working directory or reference files in the main worktree.
- Include a "Constraint: stay in your worktree" section at the top of the agent definition.
- Use a structured output format (e.g. `RESULT: complete`, `PR_URL: ...`) so the router can parse results programmatically.
- The agent must not dispatch other agents. The router owns fanout.
- Worktrees are preserved if the agent made changes, cleaned up if not. The agent does not manage its own worktree lifecycle.
- Write `.clawdio-state` in the worktree root after every phase transition. This is how the router tracks progress and resumes failed workers. Never git-commit this file.

### When to use an agent vs a skill

- **Agent**: isolated task with its own context. Needs to read code, make decisions, produce output.
- **Skill**: cross-cutting knowledge that any agent or session can invoke. Templates, checklists, conventions.

Rule of thumb: if it _does work_, it's an agent. If it _knows things_, it's a skill.

### Dispatch ownership

Only the router dispatches agents. This is an architectural invariant even when a client technically supports nested agents:

- orchestration skills return a dispatch plan to the router
- specialists do not spawn other specialists
- specialists may load available skills through the resolver in `references/dispatch-rules.md`

## Writing skills

Skills live in `skills/<name>/SKILL.md`. One directory per skill.

### Format

```markdown
---
description: One sentence. What it does and when it should be invoked.
---

# Skill Name

What this skill provides.

## Process / Content

Steps, checklists, or reference material.

## Output format

Exact format specification with examples.

## Anti-patterns

Common mistakes table.
```

### Skill arguments

Skills receive input from the current conversation. Claude Code may expose it as the Skill tool's `args` string; Codex may supply it through the invoking prompt.

- Document accepted args in an **Arguments** section immediately after the skill heading, before the process.
- Use a table: arg name, form (positional/flag/named), example.
- Support both positional (`ship #42`) and named (`ship --issue #42`) where it makes sense.
- The skill instructions parse common forms from either explicit arguments or conversation context. No client-specific parser is needed.
- Args are for common cases. Complex orchestration should use conversation context.

Example:

```markdown
## Arguments

| Arg | Form | Example |
|-|-|-|
| issue ref | positional or `--issue` | `ship #42` |
| `--resume` | flag | Resume in-progress workflow |
```

### Workflow state

Workflow skills (multi-phase, resumable) can persist state to memory between sessions.

- Write state to `memory/workflow_<skill>_<branch>.md` after each phase gate.
- Use standard memory frontmatter (`name`, `description`, `type: project`).
- Check for existing state at skill start. Offer to resume or start fresh.
- Clean up on completion: delete the state file and remove from `MEMORY.md` index.
- State files are project-scoped (in the project memory directory), not global.

State file body should be simple key-value pairs: phase, issue, branch, PR URL, timestamp.

### Conventions

- The description field drives skill discovery in both clients. Be specific about trigger phrases.
- Lead with the rule or action. Details and rationale below.
- Skills are loaded into the caller's context window, so keep them focused.
- Refer to the full namespaced identity (`clawdio:skill-name`) when the client displays namespaces.
- Include output format examples that are exact, not suggestive. Agents interpret loose formats liberally.

## Writing hooks

Hooks are registered in `hooks/hooks.json`; portable behaviour lives in `hooks/file_hook.py`. Both clients execute the same script.

The hook adapter supports Python 3.9 and newer and uses only the standard library.

### Lifecycle events

- **PreToolUse**: runs before a matched edit. Exit code 2 blocks the tool.
- **PostToolUse**: runs after a matched edit.

### Event input

- Claude Code can provide `CLAUDE_FILE_PATH` or `tool_input.file_path`.
- Codex aliases `Write|Edit` to `apply_patch`; patch paths are in `tool_input.command`.
- `file_hook.py` is the only place that should translate those forms.
- Hook commands locate the plugin with `PLUGIN_ROOT`, falling back to the compatible `CLAUDE_PLUGIN_ROOT` variable.

### Conventions

- Hooks must be fast. They run on every matching tool use.
- Hooks must be deterministic. No LLM calls, no network requests.
- Optional formatters and linters must fail silently.
- Unit-smoke the script with representative Claude and Codex JSON payloads, including a multi-file patch.
- Deliberately target `.env` and verify exit code 2 before changing sensitive-path rules.

## Personal agent overrides

Claude Code plugin agents can be overridden by placing a file with the same name in `~/.claude/agents/`. Codex-specific project context belongs in `AGENTS.md`; installed equivalent skills may also augment a specialist.

Use this for domain-specific reviewers that contain proprietary knowledge or team-specific conventions.

## Naming

- Agent names: lowercase, hyphenated. Match filename to `name` field.
- Skill names: lowercase, hyphenated directory name.
- Keep names short. `review` not `pull-request-review-coordinator`.

## External capability providers

[agent-skills](https://github.com/addyosmani/agent-skills) provides cross-cutting development skills; [dev-team-plugin](https://github.com/kuadrant/dev-team-plugin) provides feature-lifecycle workflows. Claude declares both as dependencies. Keep exact external names in canonical prompts, resolve equivalents centrally for other clients, and maintain local compositions for any externally routed workflow that clawdio promises to support.
