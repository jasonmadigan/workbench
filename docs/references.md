# References

## Shared concepts

Clawdio uses the same logical building blocks in both supported clients:

| Concept | Claude Code | Codex |
|-|-|-|
| Repository instructions | `CLAUDE.md` | `AGENTS.md` |
| Plugin manifest | `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` |
| Workflows | `skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` |
| Specialist prompts | Native plugin agents from `agents/*.md` | Built-in subagents instructed to read `agents/*.md` |
| Guardrails | `hooks/hooks.json` | `hooks/hooks.json` |
| External systems | CLI tools and MCP servers | CLI tools and MCP servers |

The shared marketplace is `.claude-plugin/marketplace.json`. Both clients can
read that location; its local `source: "."` entry points each installer back to
the repository root, where the client selects its own manifest.

## Portability contract

- `agents/*.md` and workflow skills are canonical. Do not fork them per client.
- `skills/router/SKILL.md` is the Codex entry adapter; Claude Code uses the
  native router agent.
- `references/dispatch-rules.md` maps agent roles, user decisions, worktree
  isolation, and external skill requests onto the active client.
- `hooks/file_hook.py` translates Claude file paths and Codex `apply_patch`
  payloads into one hook implementation.
- Third-party skills are external capability providers. Claude declares its
  providers as package dependencies; other clients prefer the named skill, then
  a clearly equivalent installed skill, then clawdio's documented baseline or
  composition.

## Codex primitives

- [Build plugins](https://learn.chatgpt.com/docs/build-plugins): plugin layout,
  manifests, skills, hooks, MCP servers, and marketplaces.
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents):
  built-in roles and custom-agent configuration.
- [Hooks](https://learn.chatgpt.com/docs/hooks): hook events, matchers, payloads,
  environment variables, and blocking behaviour.
- [Command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli):
  `codex plugin` and `codex mcp` commands.

## Claude Code primitives

- **CLAUDE.md**: always-on project context.
- **Skills**: on-demand workflow or reference material.
- **Subagents**: isolated specialist contexts discovered from `agents/*.md`.
- **Hooks**: deterministic pre/post tool commands.
- **MCP servers**: connectors to GitHub, Jira, browsers, and other systems.
- **Plugins**: shareable bundles described by `.claude-plugin/plugin.json`.

## Related projects

- [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills): external
  TDD, debugging, review, security, and git-workflow capabilities.
- [kuadrant/dev-team-plugin](https://github.com/kuadrant/dev-team-plugin):
  external design and feature-lifecycle capabilities.
- [github/github-mcp-server](https://github.com/github/github-mcp-server):
  GitHub issues, pull requests, Actions, and code search through MCP.
- [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action):
  Claude Code in GitHub Actions.

## Vertex authentication

The author's Claude Code environment uses Vertex AI:

```bash
CLAUDE_CODE_USE_VERTEX=1
ANTHROPIC_VERTEX_PROJECT_ID=<project-id>
CLOUD_ML_REGION=<region>
```

This is a local Claude Code configuration, not a clawdio requirement and not a
Codex authentication mechanism.
