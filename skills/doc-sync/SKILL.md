---
name: doc-sync
description: Verify and fix documentation accuracy against the actual repo contents. Use when source files change, before committing, or when asked to check docs. Works in any repo by discovering documentation files and cross-referencing against the repo.
---

# Doc Sync

Verify that all documentation accurately reflects the current state of the repo. Invoke via `clawdio:doc-sync`. Fix discrepancies found.

## Process

### Step 1: Discover documentation

Find all documentation files in the repo:

```bash
find . -maxdepth 3 -name '*.md' -not -path './.claude/*' -not -path './node_modules/*' -not -path './vendor/*' | sort
```

Key files to always check if they exist: `README.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, and any files in `docs/` or `doc/`. In this repo, check `docs/architecture.md`, `docs/contributing.md`, and `docs/references.md`.

### Step 2: Discover what's documentable

Scan the repo for things documentation typically references:

- **Directory structure**: `ls -d */` at the root
- **Entry points**: main files, manifests (`package.json`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `go.mod`, `Cargo.toml`, `Makefile`)
- **Agents/skills/hooks**: `agents/*.md`, `skills/*/SKILL.md`, `hooks/`, `.claude/`, `.codex/`, and client plugin manifests
- **Commands/targets**: `make -qp 2>/dev/null | grep '^[a-zA-Z].*:' | head -30` for Makefile targets
- **Dependencies**: package files, import statements, dependency declarations
- **Config files**: `.env.example`, config templates, env var references

### Step 3: Cross-reference

For each documentation file, check every factual claim against reality:

| Claim type | How to verify |
|-|-|
| File/directory paths mentioned | `ls` or `find` to confirm they exist |
| Commands or CLI examples | `which` or `command -v` for tools; `make -n <target>` for make targets |
| Lists of components (agents, skills, modules, packages) | Compare against actual directory listing |
| Tables cataloguing things | Verify every row exists, verify nothing is missing |
| Diagrams (mermaid, ASCII) | Verify every node/edge corresponds to reality |
| Version numbers | Compare against manifest/config files |
| Default values | Compare against source code |
| Environment variables | Grep source for actual usage |

### Step 4: Report and fix

Report findings as a table:

```
| File | Issue | Fix |
|-|-|-|
| README.md | Agents table missing worktree-worker | Add row |
| CLAUDE.md | Skills list outdated | Update list |
```

If no issues found, report: "All docs are in sync."

If issues found: fix them. Edit the documentation files to match the source of truth. The source of truth is always the code and file system, never the docs. Run `git diff` after fixing to confirm changes are correct.

## Rules

- **Accuracy, not completeness.** Verify what IS documented is correct. Don't flag undocumented features.
- **Code is the source of truth.** When docs and code disagree, the code is right. Fix the docs.
- **Check all doc files, not just one.** The same fact (e.g. list of agents) often appears in multiple files. Update all of them.
- **Diagrams go stale fastest.** Always check mermaid and ASCII diagrams against reality.
- **Read before fixing.** Always read the actual source file before editing docs. Don't fix from memory.

## Plugin-specific checks

When running in an agent plugin repo (detected by `.claude-plugin/` or `.codex-plugin/`):

- Agent catalogue: run `ls agents/*.md` and compare against any agent tables in docs
- Skill catalogue: run `ls -d skills/*/` and compare against any skill tables in docs
- Hook catalogue: read `hooks/hooks.json` and compare entries against any hook tables in docs
- Router dispatch: read `agents/router.md` and verify all dispatch targets appear in dispatch diagrams
- Plugin manifests: read every client manifest and verify documented versions. If both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` exist, their `name` and `version` must match.
- Portability adapter: when canonical prompts in `agents/` change, verify `references/dispatch-rules.md` and `skills/router/SKILL.md` still translate them without copying their bodies.
- External capabilities: document third-party skills by intent and fallback. Never duplicate their implementation or assume one client's namespace is universally installed.

## Anti-patterns

| Problem | Fix |
|-|-|
| Checking only `README.md` | Check ALL `.md` files: `CLAUDE.md`, `docs/`, `CONTRIBUTING.md`. |
| Fixing docs without reading the source | Always read the actual file with `Read` first. |
| Flagging missing documentation | Only flag inaccuracies. Missing docs is a separate concern. |
| Skipping diagrams | Diagrams go stale fastest. Always check them. |
| Reporting issues without fixing them | If you can fix it, fix it. Don't just report. |
