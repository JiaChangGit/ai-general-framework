import argparse
import json
import shutil
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
        (self.source / "scripts").mkdir()
        (self.source / "scripts/agf.py").write_text("print('fixture tools')\n", encoding="utf-8")
        (self.source / "docs").mkdir()
        for name in manage.GUIDES:
            (self.source / "docs" / name).write_text(f"Fixture guide: {name}\n", encoding="utf-8")

    def run_project(self, operation="plan", apply=False, hosts=None, skills=None, tools="copy"):
        return manage.project(argparse.Namespace(operation=operation, target=str(self.root), source=str(self.source), host=hosts, skill=["trace"] if skills is None else skills, tools=tools, apply=apply))

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
        args = parser.parse_args(["project", "plan", "--target", str(self.root), "--source", str(self.source), "--host", "claude", "--host", "opencode"])
        self.assertTrue(args.func(args)["ready"])

    def test_targeted_update_preserves_other_installed_skills(self):
        other = self.source / "skills" / "debug"
        other.mkdir()
        (other / "SKILL.md").write_text("Debug version one", encoding="utf-8")
        self.run_project("install", True, skills=["trace", "debug"])
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

    def test_added_host_receives_retained_skill_without_refreshing_it(self):
        self.run_project("install", True, hosts=["opencode"], skills=["trace"], tools="shared")
        installed = (self.root / ".agents/skills/trace/SKILL.md").read_bytes()
        (self.source / "skills/trace/SKILL.md").write_text("Newer source, not selected for refresh", encoding="utf-8")
        other = self.source / "skills/debug"
        other.mkdir()
        (other / "SKILL.md").write_text("Debug instructions", encoding="utf-8")
        self.run_project("update", True, hosts=["opencode", "claude"], skills=["debug"], tools="shared")
        self.assertEqual((self.root / ".claude/skills/trace/SKILL.md").read_bytes(), installed)
        self.assertEqual((self.root / ".agents/skills/trace/SKILL.md").read_bytes(), installed)
        self.assertTrue((self.root / ".claude/skills/debug/SKILL.md").is_file())

    def test_installed_runtime_runs_from_destination_cwd(self):
        shutil.copytree(manage.SOURCE / "agf", self.source / "agf", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(manage.SOURCE / "scripts", self.source / "scripts", dirs_exist_ok=True)
        args = argparse.Namespace(operation="install", target=str(self.root), source=str(self.source), host=["opencode"], skill=["trace"], tools="copy", apply=True)
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

    def test_new_defaults_are_shared_rules_and_guides_without_skills(self):
        parser = argparse.ArgumentParser()
        manage.register(parser.add_subparsers(required=True))
        args = parser.parse_args(["project", "install", "--target", str(self.root), "--source", str(self.source), "--apply"])
        result = args.func(args)
        self.assertEqual(result["tools_mode"], "shared")
        self.assertEqual(result["refresh_skills"], [])
        self.assertEqual(result["available_skills"], ["trace"])
        value = json.loads((self.root / ".agf/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(value["skills"], [])
        self.assertEqual(len(value["files"]), 6)
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".agf/managed/runtime").exists())
        self.assertFalse((self.root / ".agf/managed/profile.example.json").exists())
        self.assertIn(str(self.source / "scripts/agf.py"), (self.root / ".agf/managed/project-rules.md").read_text(encoding="utf-8"))

    def test_shared_status_reports_missing_tools_even_when_managed_files_are_clean(self):
        self.run_project("install", True, tools="shared")
        (self.source / "scripts/agf.py").unlink()
        result = self.run_project("status")
        self.assertTrue(result["clean"])
        self.assertFalse(result["tools_available"])
        self.assertFalse(result["ready"])
        self.assertEqual(result["_exit_code"], 1)

    def test_foreign_recorded_source_requires_explicit_native_source(self):
        self.run_project("install", True, tools="shared")
        path = self.root / ".agf/manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        # Windows would silently resolve this POSIX path against the current
        # drive/share. Linux must likewise reject an inherited Windows path.
        manifest["source"] = "/" + self.source.as_posix()[len(self.source.anchor):] if sys.platform == "win32" else "C:\\framework"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        before = path.read_bytes()
        args = argparse.Namespace(operation="update", target=str(self.root), source=None, host=None, skill=None, tools=None, apply=True)
        with self.assertRaisesRegex(AgfError, "native absolute path"):
            manage.project(args)
        self.assertEqual(path.read_bytes(), before)
        args.source = str(self.source)
        self.assertTrue(manage.project(args)["applied"])
        self.assertTrue(self.run_project("status")["ready"])

    def test_failed_create_cleans_its_partial_file_but_preserves_user_files(self):
        destination = self.root / ".agf/managed/project-rules.md"
        notes = self.root / "notes.txt"
        notes.write_text("User content", encoding="utf-8")
        original_open = Path.open

        class BrokenWrite:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def write(self, data):
                self.stream.write(data[:3])
                raise OSError("Injected write failure after partial creation")

        def open_file(path, mode="r", *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            return BrokenWrite(stream) if path == destination and mode == "xb" else stream

        with patch.object(Path, "open", open_file):
            with self.assertRaises(AgfError):
                self.run_project("install", True, tools="shared")
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / ".agf/manifest.json").exists())
        self.assertEqual(notes.read_text(encoding="utf-8"), "User content")

    def test_mode_switch_is_planned_and_rollback_restores_the_mode(self):
        self.run_project("install", True, tools="shared")
        preview = self.run_project("update", tools="copy")
        self.assertEqual(preview["previous_tools_mode"], "shared")
        self.assertTrue(any(item["path"].startswith(".agf/managed/runtime/") for item in preview["operations"]))
        self.assertFalse((self.root / ".agf/managed/runtime/scripts/agf.py").exists())
        self.run_project("update", True, tools="copy")
        self.assertTrue((self.root / ".agf/managed/runtime/scripts/agf.py").is_file())
        self.run_project("rollback", True)
        self.assertEqual(self.run_project("status")["tools_mode"], "shared")
        self.assertFalse((self.root / ".agf/managed/runtime/scripts/agf.py").is_file())

    def test_legacy_manifest_without_mode_keeps_copy_behavior(self):
        self.run_project("install", True, tools="copy")
        path = self.root / ".agf/manifest.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        del value["tools_mode"]
        path.write_text(json.dumps(value), encoding="utf-8")
        self.assertEqual(self.run_project("status")["tools_mode"], "copy")
        result = self.run_project("update", True, tools=None)
        self.assertEqual(result["tools_mode"], "copy")
        self.assertTrue((self.root / ".agf/managed/runtime/scripts/agf.py").is_file())

    def test_retired_skill_requires_apply_and_can_be_restored(self):
        self.run_project("install", True, tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        original = target.read_bytes()
        (self.source / "skills/trace/SKILL.md").unlink()
        args = argparse.Namespace(operation="update", target=str(self.root), source=None, host=None, skill=None, tools=None, apply=False)
        preview = manage.project(args)
        self.assertEqual([item["action"] for item in preview["operations"] if item["path"].endswith("trace/SKILL.md")], ["retire"])
        self.assertEqual(target.read_bytes(), original)
        args.apply = True
        manage.project(args)
        self.assertFalse(target.exists())
        self.assertEqual(self.run_project("status")["skills"], [])
        self.run_project("rollback", True)
        self.assertEqual(target.read_bytes(), original)

    def test_empty_selection_does_not_install_new_skills_after_retirement(self):
        self.run_project("install", True, skills=[], tools="shared")
        args = argparse.Namespace(operation="update", target=str(self.root), source=None, host=None, skill=None, tools=None, apply=True)
        manage.project(args)
        self.assertEqual(self.run_project("status")["skills"], [])
        self.assertFalse((self.root / ".agents").exists())

    def test_drift_blocks_retirement(self):
        self.run_project("install", True)
        target = self.root / ".agents/skills/trace/SKILL.md"
        target.write_text("local edit", encoding="utf-8")
        (self.source / "skills/trace/SKILL.md").unlink()
        with self.assertRaises(AgfError):
            manage.project(argparse.Namespace(operation="update", target=str(self.root), source=None, host=None, skill=None, tools=None, apply=True))
        self.assertEqual(target.read_text(encoding="utf-8"), "local edit")


if __name__ == "__main__":
    unittest.main()
