import os
import unittest
from pathlib import Path
from unittest.mock import patch

from hooks.file_hook import edited_paths, is_plugin_definition, is_sensitive


class EditedPathsTest(unittest.TestCase):
    def test_reads_claude_file_path(self) -> None:
        with patch.dict(os.environ, {"CLAUDE_FILE_PATH": "src/app.py"}, clear=True):
            self.assertEqual(edited_paths({}), [Path("src/app.py")])

    def test_reads_all_codex_apply_patch_paths(self) -> None:
        event = {
            "tool_input": {
                "command": """*** Begin Patch
*** Update File: agents/router.md
*** Add File: skills/router/SKILL.md
*** End Patch"""
            }
        }
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                edited_paths(event),
                [Path("agents/router.md"), Path("skills/router/SKILL.md")],
            )


class PathPolicyTest(unittest.TestCase):
    def test_sensitive_path_patterns_match_original_hook_policy(self) -> None:
        sensitive = (
            ".env",
            "service.env",
            "service.env.production",
            "backup-credentials.json",
            "private.pem",
            "keys/id_rsa.pub",
        )
        for value in sensitive:
            with self.subTest(value=value):
                self.assertTrue(is_sensitive(Path(value)))
        self.assertFalse(is_sensitive(Path(".envrc")))

    def test_plugin_definitions_support_relative_and_absolute_paths(self) -> None:
        definitions = (
            "agents/router.md",
            "skills/router/SKILL.md",
            "/tmp/clawdio/.codex-plugin/plugin.json",
            "/tmp/clawdio/hooks/file_hook.py",
        )
        for value in definitions:
            with self.subTest(value=value):
                self.assertTrue(is_plugin_definition(Path(value)))
        self.assertFalse(is_plugin_definition(Path("src/router.py")))


if __name__ == "__main__":
    unittest.main()
