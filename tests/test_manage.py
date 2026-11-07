import argparse
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from agf import manage
from agf.common import AgfError


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix=".agf-manage-test-", dir=manage.SOURCE)
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.source = base / "source"
        self.root = base / "專案 with spaces & $"
        self.root.mkdir()
        skill = self.source / "skills" / "trace"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: trace\ndescription: Trace a repository\n---\nRead evidence.\n", encoding="utf-8")
        (self.source / "templates").mkdir()
        (self.source / "templates" / "project-rules.md").write_text("Keep task scope.\n", encoding="utf-8")

    def run_project(self, operation="plan", apply=False, hosts=None, skills=None):
        return manage.project(argparse.Namespace(operation=operation, target=str(self.root), source=str(self.source), host=hosts, skill=skills, apply=apply))

    def test_plan_is_read_only_and_uses_opencode_by_default(self):
        result = self.run_project()
        self.assertTrue(result["ready"])
        self.assertEqual(result["hosts"], ["opencode"])
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertFalse(result["applied"])

    def test_install_is_dry_run_without_apply(self):
        self.run_project("install")
        self.assertFalse((self.root / ".agf").exists())

    def test_install_all_hosts_and_status(self):
        result = self.run_project("install", True, list(manage.HOSTS))
        self.assertTrue(result["applied"])
        self.assertEqual((self.root / ".agents/skills/trace/SKILL.md").read_bytes(), (self.root / ".claude/skills/trace/SKILL.md").read_bytes())
        self.assertIn("@AGENTS.md", (self.root / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("@AGENTS.md", (self.root / "GEMINI.md").read_text(encoding="utf-8"))
        status = self.run_project("status")
        self.assertTrue(status["clean"])
        self.assertGreaterEqual(status["managed_files"], 6)

    def test_preserves_existing_rules_without_claiming_automatic_integration(self):
        original = b"Existing project rules\r\n"
        for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            (self.root / name).write_bytes(original)
        result = self.run_project("install", True, list(manage.HOSTS))
        self.assertEqual(len(result["notices"]), 3)
        for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            self.assertEqual((self.root / name).read_bytes(), original)
        self.run_project("rollback", True)
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), original)

    def test_existing_unmanaged_skill_is_not_overwritten_even_if_identical(self):
        path = self.root / ".agents/skills/trace/SKILL.md"
        path.parent.mkdir(parents=True)
        original = (self.source / "skills/trace/SKILL.md").read_bytes()
        path.write_bytes(original)
        self.assertFalse(self.run_project()["ready"])
        with self.assertRaises(AgfError):
            self.run_project("install", True)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((self.root / ".agf").exists())

    def test_update_and_rollback_restore_actual_previous_bytes(self):
        self.run_project("install", True)
        first = (self.root / ".agents/skills/trace/SKILL.md").read_bytes()
        (self.source / "skills/trace/SKILL.md").write_bytes(first + b"New instructions.\r\n")
        self.run_project("update", True)
        self.assertNotEqual((self.root / ".agents/skills/trace/SKILL.md").read_bytes(), first)
        dry = self.run_project("rollback")
        self.assertTrue(dry["ready"])
        self.assertFalse(dry["applied"])
        self.run_project("rollback", True)
        self.assertEqual((self.root / ".agents/skills/trace/SKILL.md").read_bytes(), first)
        self.assertTrue(self.run_project("status")["clean"])
        self.run_project("rollback", True)
        self.assertFalse((self.root / ".agf/manifest.json").exists())

    def test_drift_blocks_both_update_and_rollback(self):
        self.run_project("install", True)
        path = self.root / ".agents/skills/trace/SKILL.md"
        path.write_text("Local work", encoding="utf-8")
        self.assertFalse(self.run_project("status")["clean"])
        for operation in ("update", "rollback"):
            self.assertFalse(self.run_project(operation)["ready"])
            with self.assertRaises(AgfError):
                self.run_project(operation, True)
        self.assertEqual(path.read_text(encoding="utf-8"), "Local work")

    def test_initial_rollback_preserves_unmanaged_contents(self):
        self.run_project("install", True)
        other = self.root / ".agents/skills/personal.txt"
        other.write_text("my content", encoding="utf-8")
        self.run_project("rollback", True)
        self.assertEqual(other.read_text(encoding="utf-8"), "my content")
        self.assertFalse((self.root / ".agents/skills/trace/SKILL.md").exists())

    def test_removed_managed_file_reappearing_blocks_rollback(self):
        self.run_project("install", True, ["claude"])
        self.run_project("update", True, ["opencode"])
        path = self.root / "CLAUDE.md"
        path.write_text("new local rules", encoding="utf-8")
        self.assertFalse(self.run_project("rollback")["ready"])
        with self.assertRaises(AgfError):
            self.run_project("rollback", True)
        self.assertEqual(path.read_text(encoding="utf-8"), "new local rules")

    def test_idempotent_update_does_not_create_another_transaction(self):
        first = self.run_project("install", True)
        result = self.run_project("update", True)
        self.assertTrue(result["unchanged"])
        manifest = json.loads((self.root / ".agf/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["transaction"], first["transaction"])

    def test_manifest_cannot_escape_target(self):
        self.run_project("install", True)
        path = self.root / ".agf/manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["files"][".agents/skills/../../outside.txt"] = {"sha256": "0" * 64}
        path.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(AgfError):
            self.run_project("status")

    def test_failed_update_restores_previous_managed_contents(self):
        self.run_project("install", True)
        before = (self.root / ".agents/skills/trace/SKILL.md").read_bytes()
        (self.source / "skills/trace/SKILL.md").write_bytes(before + b"change")
        original = manage._replace_bytes
        failed = False

        def fail_once(path, data):
            nonlocal failed
            if path.name == "manifest.json" and not failed:
                failed = True
                raise OSError("simulated disk failure")
            return original(path, data)

        with patch.object(manage, "_replace_bytes", side_effect=fail_once):
            with self.assertRaises(AgfError):
                self.run_project("update", True)
        self.assertEqual((self.root / ".agents/skills/trace/SKILL.md").read_bytes(), before)
        self.assertTrue(self.run_project("status")["clean"])

    def test_invalid_source_does_not_create_target_files(self):
        (self.source / "skills/trace/SKILL.md").unlink()
        with self.assertRaises(AgfError):
            self.run_project("install", True)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_doctor_does_not_confuse_executable_with_authentication(self):
        with patch.object(manage.shutil, "which", return_value="/fake/tool"):
            result = manage.doctor(argparse.Namespace(host="opencode"))
        self.assertTrue(result["hosts"]["opencode"]["available_on_path"])
        self.assertEqual(result["hosts"]["opencode"]["authentication"], "not_checked")
        self.assertEqual(result["hosts"]["opencode"]["native_integration"], "not_executed")

    def test_parser_registers_all_project_operations(self):
        parser = argparse.ArgumentParser()
        manage.register(parser.add_subparsers(required=True))
        args = parser.parse_args(["project", "plan", "--target", str(self.root), "--host", "claude", "--host", "opencode"])
        self.assertTrue(args.func(args)["ready"])

    def test_targeted_update_preserves_other_installed_skills(self):
        other = self.source / "skills" / "debug"
        other.mkdir()
        (other / "SKILL.md").write_text("Debug version one", encoding="utf-8")
        self.run_project("install", True)
        (other / "SKILL.md").write_text("Debug version two", encoding="utf-8")
        trace = self.source / "skills/trace/SKILL.md"
        trace.write_text("Trace version two", encoding="utf-8")
        result = self.run_project("update", True, skills=["trace"])
        self.assertEqual(result["refresh_skills"], ["trace"])
        self.assertEqual((self.root / ".agents/skills/debug/SKILL.md").read_text(encoding="utf-8"), "Debug version one")
        self.assertEqual((self.root / ".agents/skills/trace/SKILL.md").read_text(encoding="utf-8"), "Trace version two")

    def test_selective_install_and_unknown_skill(self):
        other = self.source / "skills" / "debug"
        other.mkdir()
        (other / "SKILL.md").write_text("Debug instructions", encoding="utf-8")
        with self.assertRaises(AgfError):
            self.run_project("install", skills=["does-not-exist"])
        self.assertEqual(list(self.root.iterdir()), [])
        self.run_project("install", True, skills=["trace"])
        self.assertTrue((self.root / ".agents/skills/trace/SKILL.md").is_file())
        self.assertFalse((self.root / ".agents/skills/debug").exists())

    def test_installed_runtime_runs_from_destination_cwd(self):
        available = sorted((manage.SOURCE / "skills").glob("*/SKILL.md"))
        self.assertTrue(available, "A real framework skill is required for this end-to-end check")
        args = argparse.Namespace(operation="install", target=str(self.root), source=str(manage.SOURCE), host=["opencode"], skill=[available[0].parent.name], apply=True)
        manage.project(args)
        cli = self.root / ".agf/managed/runtime/scripts/agf.py"
        for command in (["doctor", "--host", "opencode"], ["files", "--help"], ["diagram", "--help"]):
            with self.subTest(command=command):
                process = subprocess.run([sys.executable, str(cli), *command], cwd=self.root, capture_output=True, encoding="utf-8", timeout=30, check=False)
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = json.loads(subprocess.run([sys.executable, str(cli), "doctor"], cwd=self.root, capture_output=True, encoding="utf-8", timeout=30, check=True).stdout)
        self.assertEqual(result["hosts"]["opencode"]["authentication"], "not_checked")
        manifest = json.loads((self.root / ".agf/manifest.json").read_text(encoding="utf-8"))
        self.assertIn(".agf/managed/runtime/agf/cli.py", manifest["files"])
        self.assertNotIn(".agf/managed/runtime/.agf", manifest["files"])


if __name__ == "__main__":
    unittest.main()
