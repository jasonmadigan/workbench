"""Portable file hooks for Claude Code and Codex.

Both clients send hook events as JSON on stdin, but they expose edited paths in
slightly different places.  Keep that translation here so hooks/hooks.json and
the workflow prompts do not need client-specific copies.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PATCH_PATH_RE = re.compile(
    r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$", re.MULTILINE
)
DIFF_PATH_RE = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)


def read_event() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def edited_paths(event: dict[str, Any]) -> list[Path]:
    """Return edited paths from either client's hook payload."""
    candidates: list[str] = []

    for env_name in ("CLAUDE_FILE_PATH", "CODEX_FILE_PATH"):
        if value := os.environ.get(env_name):
            candidates.append(value)

    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("file_path", "filePath", "path"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                candidates.append(value)

        command = tool_input.get("command")
        if isinstance(command, str):
            candidates.extend(PATCH_PATH_RE.findall(command))
            candidates.extend(DIFF_PATH_RE.findall(command))

    paths: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.strip().strip('"')
        if normalized == "/dev/null" or normalized in seen:
            continue
        seen.add(normalized)
        paths.append(Path(normalized))
    return paths


def is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.endswith((".env", "credentials.json"))
        or ".env." in name
        or path.suffix.lower() in {".pem", ".key", ".secret"}
        or "id_rsa" in path.as_posix().lower()
    )


def is_plugin_definition(path: Path) -> bool:
    normalized = path.as_posix().removeprefix("./")
    parts = Path(normalized).parts
    exact_targets = {
        "hooks/hooks.json",
        "hooks/file_hook.py",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "references/dispatch-rules.md",
    }
    return (
        ("agents" in parts and path.suffix == ".md")
        or ("skills" in parts and path.name == "SKILL.md")
        or any(
            normalized == target or normalized.endswith(f"/{target}")
            for target in exact_targets
        )
    )


def run_quietly(command: list[str]) -> None:
    try:
        subprocess.run(
            command,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def has_any(patterns: tuple[str, ...]) -> bool:
    root = Path.cwd()
    return any(any(root.glob(pattern)) for pattern in patterns)


def block_sensitive(paths: list[Path]) -> int:
    blocked = [str(path) for path in paths if is_sensitive(path)]
    if not blocked:
        return 0
    print(
        "BLOCK: writing to sensitive file is not allowed: " + ", ".join(blocked),
        file=sys.stderr,
    )
    return 2


def remind_docs(paths: list[Path]) -> int:
    changed = [path.name for path in paths if is_plugin_definition(path)]
    if changed:
        print(
            "DOC SYNC: plugin definitions changed "
            f"({', '.join(changed)}). Update the catalogues and conventions in "
            "README.md/docs, then keep .claude-plugin/plugin.json and "
            ".codex-plugin/plugin.json versions in sync.",
            file=sys.stderr,
        )
    return 0


def format_files(paths: list[Path]) -> int:
    prettier = has_any(
        (
            ".prettierrc",
            ".prettierrc.*",
            "prettier.config.*",
        )
    )
    clang_format = Path(".clang-format").exists()

    for path in paths:
        if not path.exists():
            continue
        if prettier:
            run_quietly(["npx", "prettier", "--write", str(path)])
        elif clang_format:
            run_quietly(["clang-format", "-i", str(path)])
        elif path.suffix == ".go" and shutil.which("gofmt"):
            run_quietly(["gofmt", "-w", str(path)])
    return 0


def lint_files(paths: list[Path]) -> int:
    eslint = has_any((".eslintrc", ".eslintrc.*", "eslint.config.*"))
    for path in paths:
        if not path.exists():
            continue
        if path.suffix == ".go" and shutil.which("golangci-lint"):
            run_quietly(["golangci-lint", "run", str(path)])
        elif path.suffix in {".js", ".ts", ".jsx", ".tsx"} and eslint:
            run_quietly(["npx", "eslint", str(path)])
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: file_hook.py block|docs|format|lint", file=sys.stderr)
        return 2

    paths = edited_paths(read_event())
    actions = {
        "block": block_sensitive,
        "docs": remind_docs,
        "format": format_files,
        "lint": lint_files,
    }
    action = actions.get(sys.argv[1])
    if action is None:
        print(f"unknown hook action: {sys.argv[1]}", file=sys.stderr)
        return 2
    return action(paths)


if __name__ == "__main__":
    raise SystemExit(main())
