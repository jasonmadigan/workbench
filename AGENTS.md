# Repository instructions

Clawdio supports Claude Code and Codex from one set of workflow sources.

## Sources of truth

- `agents/*.md`: canonical specialist behaviour and routing policy
- `skills/*/SKILL.md`: portable workflow behaviour
- `references/dispatch-rules.md`: the only client-adaptation and external-skill
  resolution layer
- `hooks/hooks.json` and `hooks/file_hook.py`: shared lifecycle configuration
  and implementation
- `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`: client manifests;
  keep their name and version in sync

Do not copy agent bodies into Codex skills or custom-agent files. The Codex
router skill loads the canonical Markdown files at runtime.

## Editing

- Preserve British English and the terse comment style documented in
  `CLAUDE.md`.
- Keep third-party capability requests intent-based. Add a portable fallback in
  `references/dispatch-rules.md`; do not vendor or rewrite another plugin's
  skill.
- Update README, architecture, contributor, and reference docs when a manifest,
  agent, skill, hook, or compatibility rule changes.
- Bump both plugin manifests together for a released behaviour change.

## Checks

Run these before handing off changes:

```bash
claude plugin validate .
python3 /path/to/plugin-creator/scripts/validate_plugin.py .
uvx skillsaw lint
python3 -m py_compile hooks/file_hook.py
python3 -m unittest hooks/test_file_hook.py
```

Resolve the plugin-creator path from the installed Codex skill; do not commit a
machine-specific path.
