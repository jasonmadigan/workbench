# Cursor client support -- design

Status: approved (scope + router-bypass call), pending spec review
Date: 2026-08-19

## Goal

Add Cursor as a third client alongside Claude Code and Codex, at the same
depth as the existing Codex adapter: router dispatch, specialist agents,
workflow skills, and file hooks all reachable from a local Cursor install.

## Why this is tractable

Cursor's plugin model (confirmed against current `cursor.com/docs`, Feb 2026
release) is closer to Claude Code's than Codex's:

- **Skills**: `SKILL.md` with `name`/`description` frontmatter -- the same
  Agent Skills open standard clawdio already uses. `skills/*/SKILL.md` needs
  no changes.
- **Agents**: markdown files with `name`/`description` (+ optional `model`,
  `readonly`, `is_background`) frontmatter, discovered from a plugin's
  `agents/` directory. clawdio's `agents/*.md` files are already in this
  shape -- unlike Codex, Cursor can load them as native subagents directly,
  no read-the-file-yourself indirection needed.
- **Plugin manifest**: `.cursor-plugin/plugin.json`, default component paths
  (`agents/`, `skills/`, `hooks/hooks.json`) match clawdio's existing layout.
- **Dispatch**: automatic (description match) or explicit `/name` or naming
  the agent in chat. Nesting is capped at one level -- main agent and its
  direct subagents can dispatch further subagents; a subagent launched by a
  subagent cannot. This already matches clawdio's "router owns dispatch,
  specialists don't fan out further" invariant with no compromise needed.

Net effect: no new agent or skill content. This is a manifest, a
dispatch-rules.md section, and a hooks adapter -- not a content fork.

## Non-goals

- No changes to `agents/*.md` or `skills/*/SKILL.md` content.
- No attempt to suppress Cursor's native auto-delegation (see decision below).
- No MCP server bundling in the new manifest -- GitHub/Atlassian MCP stay a
  documented dependency, same as today for Claude Code and Codex.
- No `dependencies` field in the Cursor manifest for `agent-skills`/`kdt`.
  Cursor's plugin.json schema doesn't support inter-plugin dependencies;
  `dispatch-rules.md`'s existing fallback-composition table already covers
  "capability absent on this client" generically, no Cursor-specific case
  needed.

## Decision: router bypass via auto-delegation

Cursor's top-level agent can auto-invoke any subagent by description match,
with no explicit-tool-call gate like Claude's Agent tool. A Cursor user
saying "review this PR" could get `clawdio:code-reviewer` directly, skipping
the router.

**Accepted.** Direct single-specialist auto-invocation is a feature, not a
gap -- the same shortcut Claude Code itself gives. The router is only
load-bearing for multi-specialist orchestration (review fanout,
parallel-ship, verify-findings), because that merge/verify/classify logic
lives in the router and orchestration skills, not in any specialist agent.
A specialist invoked directly still behaves correctly on its own; it just
doesn't get fanout, verification, or cross-specialist merging. Document this
boundary explicitly in `dispatch-rules.md` so it reads as intentional.

## Components

### 1. `.cursor-plugin/plugin.json` (new)

Mirrors `.codex-plugin/plugin.json`: `name`, `description`, `version`
(synced with the other two manifests), `author`, `repository`, `license`.
Adds `agents`, `skills`, `hooks` pointer fields at `./agents/`, `./skills/`,
`./hooks/cursor-hooks.json`.

### 2. `references/dispatch-rules.md`

- New `### Cursor` subsection under **Agent dispatch**, parallel to the
  existing `### Codex` one: native subagent dispatch, `/name` and
  natural-language invocation, the one-level nesting ceiling, and the
  router-bypass decision above.
- Cursor row/clause under **User decisions**: no confirmed structured
  multi-choice control in Cursor's docs -- fall back to one concise
  plain-text question and wait, same fallback already specified for Codex.
- Cursor bullet under **Skill loading -> Invocation syntax**: invoke via
  `/clawdio:<skill>` or natural language naming the skill; preserve the
  `clawdio:` namespace when the client displays one. **Verify at
  implementation time** whether Cursor prefixes plugin-sourced skills with
  the plugin name in its `/` picker the way Claude Code does -- docs
  confirmed skill discovery and invocation mechanics but not this specific
  namespacing behaviour.

### 3. Hooks

Cursor's hook event names are camelCase (`preToolUse`, `postToolUse`, ...)
over a JSON-over-stdin/stdout payload, distinct from Claude Code's
`PreToolUse`/`PostToolUse` shape that `hooks/hooks.json` already uses. Single
shared file can't cover both.

- New `hooks/cursor-hooks.json`, registering `preToolUse` (matcher for the
  write/edit-equivalent tool) and `postToolUse`, same three actions
  (`block`, `docs`, `format`, `lint`) as the existing Claude config.
- New normalisation branch in `hooks/file_hook.py` for Cursor's payload
  shape, following the same pattern already used to handle Codex's
  `apply_patch` aliasing. Exit-code contract (0 = ok, 2 = block) already
  matches Claude's, so blocking semantics need no new logic, only payload
  field extraction.
- **Verify at implementation time**: exact JSON field names in Cursor's
  `preToolUse`/`postToolUse` payload (tool name field, file path field).
  Docs confirmed the event names and the base envelope fields
  (`conversation_id`, `hook_event_name`, `workspace_roots`, etc.) but not the
  full per-event schema -- read the live payload (or `cursor.com/docs/hooks`
  event-specific examples) before writing the branch.

### 4. Docs

Run `clawdio:doc-sync` after the above lands. It already sweeps README,
AGENTS.md, `docs/architecture.md`, and manifest version parity on any
agents/skills/hooks/manifest change -- no separate manual doc pass planned.
Specifically expect updates to:

- `docs/architecture.md`: client capability table, dispatch table,
  portability diagram, agent/skill catalogues (mention Cursor alongside
  Claude Code/Codex).
- `docs/contributing.md`: bump-both-manifests step becomes bump-all-three;
  smoke-test step gains a Cursor local-plugin reload step; hook lifecycle
  section gains a one-line Cursor event-name caveat; personal-override
  section gains `~/.cursor/agents/` alongside `~/.claude/agents/`.
- `AGENTS.md`: manifest list gains the third file.

### 5. Local verification

Cursor doesn't auto-discover a repo's own `.cursor-plugin/` on open --
unlike Claude Code, there's no workspace-native plugin loading. Local dev
plugins load from `~/.cursor/plugins/local/<name>`, so:

```sh
ln -s ~/Work/clawdio ~/.cursor/plugins/local/clawdio
```

then reload Cursor ("Developer: Reload Window" or restart). User confirms
the router and at least one specialist agent are visible/invocable, and that
`/clawdio:next` (or similar) loads correctly.

## Testing plan

- `claude plugin validate --strict .` and the plugin-creator validator still
  pass (unaffected by an additive manifest).
- `python3 -m unittest hooks/test_file_hook.py` extended with representative
  Cursor payloads (mirrors the existing Claude/Codex payload tests), once
  the real payload shape is confirmed.
- `uvx skillsaw lint` unaffected (no skill content changes).
- Manual: symlink + reload per above, dispatch router, dispatch one
  specialist directly (confirms the accepted auto-delegation path), trigger
  a `.env` write to confirm `block-env-writes` fires under Cursor's hook
  shape.

## Open risks

1. Cursor skill `/` picker namespacing for plugin-sourced skills --
   unconfirmed, verify before finalising the Invocation syntax wording.
2. Exact `preToolUse`/`postToolUse` payload field names -- unconfirmed,
   verify before writing the `file_hook.py` branch.
3. No local Cursor instance in this session to test against directly; the
   user verifies steps under "Local verification" and "Testing plan ->
   Manual" themselves after implementation.
