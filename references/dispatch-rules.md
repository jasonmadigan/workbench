# Dispatch Rules

Cross-cutting rules for agents and skills that dispatch subagents, load other
skills, or interact with users. This file is the portability boundary between
Claude Code and Codex; keep client-specific mechanics here instead of copying
them into every workflow.

## Canonical sources

- `agents/*.md` contains specialist behaviour. Do not duplicate those prompts in
  Codex adapters or custom-agent files.
- `skills/*/SKILL.md` contains workflow behaviour shared by both clients.
- This file maps those logical agents and skills onto the tools exposed by the
  active client.

Relative paths in a skill are resolved from that skill's `SKILL.md`, not from
the user's working repository.

## Agent dispatch

Dispatch by role, not by a hard-coded tool name.

### Claude Code

Use the Agent tool with `subagent_type: "clawdio:<agent>"`. Never pass `name`:
named Claude agents enter mailbox mode and can sit idle. Track the returned
`agentId`.

### Codex

Codex plugins discover skills and hooks, but not Claude's `agents/*.md` files as
custom agents. The clawdio router therefore treats each Markdown agent as a
canonical prompt resource:

1. Resolve `../agents/<agent>.md` and this file to absolute paths from the
   plugin root. From `skills/router/SKILL.md`, those paths are
   `../../agents/<agent>.md` and `../../references/dispatch-rules.md`.
2. Spawn a built-in Codex subagent and tell it to read this file first, then the
   selected agent file, before doing the task. Pass the user's full issue or PR
   context unchanged.
3. Use `worker` for implementation, feedback fixes, tests, docs, and isolated
   shipping work; `explorer` for read-only classification; and `default` for
   review, verification, triage, refinement, and release notes.
4. Do not pin a model or reasoning effort unless the user explicitly asks.

If the runtime cannot spawn subagents, run a single-agent version of the
workflow and say that the fanout was unavailable. Never claim that specialists
ran when they did not.

Only run write-heavy agents concurrently when each has an isolated worktree.
Use native worktree isolation when the client exposes it; otherwise create and
verify separate git worktrees before dispatch. Pass each manual worktree's
absolute path to its worker and require that path as the working directory for
every command. If the adapter cannot guarantee the starting directory, the
worker must verify it with `git rev-parse --show-toplevel` before editing. Run
the writers serially if any of those checks fail.

## User decisions

Use the active client's structured user-input control when one is available.
In Claude Code this is `AskUserQuestion`. In Codex, use its user-input control
when exposed; otherwise ask one concise plain-text question and wait. Never
pretend a clickable choice was shown.

This applies to post/edit/don't-post, draft/ready, next-step suggestions, issue
selection, and merge confirmation. External writes still require explicit user
approval.

## Skill loading

Treat a namespaced skill as a capability request, not as an assumption that a
particular third-party plugin is installed.

1. Prefer the exact namespaced skill named by the workflow.
2. If it is unavailable, use an installed skill that clearly provides the same
   capability.
3. If no equivalent is installed, use the local agent or skill procedure where
   it is self-contained. State which optional enhancement was unavailable.
4. Do not invoke an unrelated bare skill merely because its short name matches.

The Claude package declares `agent-skills` as a dependency. On clients where
that exact provider is unavailable, Clawdio's agent definitions contain the
baseline process: continue with it when an equivalent TDD, review, security,
debugging, or git skill is absent.

The Claude package also declares `kdt`; other clients may not have it. When its
external workflows are absent, use these local compositions rather than
copying kdt into this repository:

| Requested capability | Portable fallback |
|-|-|
| `kdt:feature-design` | refine agent, then docs agent |
| `kdt:feature-implement` | implement agent |
| `kdt:pr-closes-issue` | code-reviewer plus test-verifier |
| `kdt:external-contribs` | `clawdio:next` with external-contribution scope |

### Invocation syntax

- Claude Code: invoke the full name through the Skill tool, for example
  `clawdio:ship`; never shorten it to `ship`.
- Codex: load or request the installed namespaced skill using the skill
  mechanism exposed by the client. Preserve the `clawdio:` or external plugin
  namespace when the client displays one.

If loaded content does not match the requested capability, stop and resolve the
correct namespaced skill before continuing.
