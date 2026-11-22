import argparse
import json
import os
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

    def test_update_without_an_install_names_the_target(self):
        with self.assertRaises(AgfError) as caught:
            self.run_project("update", True)
        self.assertIn(str(self.root.resolve()), str(caught.exception))
        self.assertIn("project plan", str(caught.exception))

    def test_the_home_directory_is_not_suggested_as_a_place_to_install(self):
        with patch.object(manage.Path, "home", return_value=self.root.resolve()):
            with self.assertRaises(AgfError) as caught:
                self.run_project("update", True)
            notices = self.run_project("plan")["notices"]
        message = str(caught.exception)
        self.assertIn("home directory", message)
        self.assertIn("--target", message)
        self.assertNotIn("use project install", message)
        self.assertTrue(any("home directory" in notice for notice in notices), notices)
        self.assertFalse((self.root / ".agf").exists())

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

    def test_status_warns_while_an_existing_claude_md_only_mentions_the_rules(self):
        (self.root / "CLAUDE.md").write_text("Notes. Rules live in `.agf/managed/project-rules.md`.\n", encoding="utf-8")
        result = self.run_project("install", True, ["claude"])
        notice = next(item for item in result["notices"] if item.startswith("Preserved existing CLAUDE.md"))
        self.assertIn("`@.agf/managed/project-rules.md`", notice)
        status = self.run_project("status")
        self.assertEqual(status["rule_entries"], [{"path": "CLAUDE.md", "hosts": ["claude"], "rules": "mentioned"}])
        self.assertEqual(len(status["warnings"]), 1)
        self.assertIn("`@.agf/managed/project-rules.md`", status["warnings"][0])
        self.assertTrue(status["clean"])
        self.assertEqual(status["_exit_code"], 0)

    def test_status_follows_imports_relative_to_the_importing_file(self):
        (self.root / "CLAUDE.md").write_text("@docs/rules.md\n", encoding="utf-8")
        (self.root / "docs").mkdir()
        (self.root / "docs/rules.md").write_text("Shared rules.\n", encoding="utf-8")
        self.run_project("install", True, ["claude"])
        self.assertEqual(self.run_project("status")["rule_entries"][0]["rules"], "not_found")
        (self.root / "docs/rules.md").write_text("Shared rules.\n@../.agf/managed/project-rules.md\n", encoding="utf-8")
        status = self.run_project("status")
        self.assertEqual(status["rule_entries"][0]["rules"], "imported")
        self.assertEqual(status["warnings"], [])

    def test_imports_inside_code_are_not_imports(self):
        (self.root / "CLAUDE.md").write_text("```\n@.agf/managed/project-rules.md\n```\nWrite `@.agf/managed/project-rules.md` to import.\nMail admin@example.com.\n", encoding="utf-8")
        self.run_project("install", True, ["claude"])
        self.assertEqual(self.run_project("status")["rule_entries"][0]["rules"], "mentioned")

    def test_dot_claude_entry_counts_for_claude(self):
        (self.root / "CLAUDE.md").write_text("Notes only.\n", encoding="utf-8")
        (self.root / ".claude").mkdir()
        (self.root / ".claude/CLAUDE.md").write_text("@../.agf/managed/project-rules.md\n", encoding="utf-8")
        self.run_project("install", True, ["claude"])
        status = self.run_project("status")
        self.assertEqual(status["rule_entries"], [{"path": ".claude/CLAUDE.md", "hosts": ["claude"], "rules": "imported"}])
        self.assertEqual(status["warnings"], [])

    def test_generated_entries_load_the_rules_for_every_host(self):
        self.run_project("install", True, list(manage.HOSTS))
        status = self.run_project("status")
        self.assertEqual(status["warnings"], [])
        self.assertEqual([(entry["path"], entry["hosts"], entry["rules"]) for entry in status["rule_entries"]],
                         [("AGENTS.md", ["codex", "opencode"], "mentioned"), ("CLAUDE.md", ["claude"], "imported"), ("GEMINI.md", ["gemini"], "imported")])

    def test_status_warns_when_agents_md_does_not_point_to_the_rules(self):
        (self.root / "AGENTS.md").write_text("Project rules only.\n", encoding="utf-8")
        result = self.run_project("install", True, ["codex"])
        self.assertIn("does not mention .agf/managed/project-rules.md", result["notices"][0])
        status = self.run_project("status")
        self.assertEqual(status["rule_entries"], [{"path": "AGENTS.md", "hosts": ["codex"], "rules": "not_found"}])
        self.assertEqual(len(status["warnings"]), 1)
        self.assertEqual(status["_exit_code"], 0)

    def test_import_depth_stops_at_five_hops_like_claude_code(self):
        for hops, expected in ((5, "imported"), (6, "not_found")):
            with self.subTest(hops=hops):
                chain = self.root / f"chain{hops}"
                chain.mkdir()
                (self.root / "CLAUDE.md").write_text(f"@chain{hops}/1.md\n", encoding="utf-8")
                for step in range(1, hops):
                    target = f"{step + 1}.md" if step + 1 < hops else "../.agf/managed/project-rules.md"
                    (chain / f"{step}.md").write_text(f"@{target}\n", encoding="utf-8")
                self.assertEqual(manage._rules_state(self.root, "CLAUDE.md", follow=True), expected)

    def test_unusable_import_tokens_are_skipped(self):
        (self.root / "CLAUDE.md").write_text("@bad\x00name\n@also/../../../../../../../../nowhere\n", encoding="utf-8")
        self.assertEqual(manage._rules_state(self.root, "CLAUDE.md", follow=True), "not_found")

    def test_status_notes_a_parent_directory_with_its_own_claude_code_files(self):
        # S8 and S10 started sessions one level up; the project's skills and deny rules did not load.
        self.run_project("install", True, ["claude"])
        parent = self.root.parent
        (parent / ".claude").mkdir()
        (parent / ".claude" / "settings.json").write_text("{}", encoding="utf-8")
        status = self.run_project("status")
        mine = [item for item in status["parent_claude_dirs"] if item["path"] == str(parent)]
        self.assertEqual(mine, [{"path": str(parent), "files": [".claude/settings.json"]}])
        self.assertTrue(any(str(parent) in notice and "Start Claude Code from" in notice for notice in status["launch_notices"]))
        self.assertEqual(status["warnings"], [], "a notice, not a warning: the project itself is fine")
        shutil.rmtree(parent / ".claude")
        self.assertFalse([item for item in self.run_project("status")["parent_claude_dirs"] if item["path"] == str(parent)])

    def test_status_without_installation_has_no_rule_entries(self):
        status = self.run_project("status")
        self.assertEqual((status["rule_entries"], status["warnings"]), ([], []))

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

    def test_update_preserves_edit_after_preflight(self):
        self.run_project("install", True, tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        manifest = self.root / ".agf/manifest.json"
        original_manifest = manifest.read_bytes()
        (self.source / "skills/trace/SKILL.md").write_bytes(target.read_bytes() + b" source update")
        original = manage._write_snapshot
        def concurrent_edit(root, path, text):
            if path.parent.name == "history":
                target.write_bytes(b"user edit after preflight")
            return original(root, path, text)
        with patch.object(manage, "_write_snapshot", side_effect=concurrent_edit):
            with self.assertRaisesRegex(AgfError, "changed during operation"):
                self.run_project("update", True, tools="shared")
        self.assertEqual(target.read_bytes(), b"user edit after preflight")
        self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_create_appearing_after_plan_is_preserved(self):
        self.run_project("install", True, skills=[], tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        original = manage._plan
        def concurrent_create(*args):
            plan = original(*args)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"another process created this")
            return plan
        with patch.object(manage, "_plan", side_effect=concurrent_create):
            with self.assertRaisesRegex(AgfError, "appeared after planning"):
                self.run_project("update", True, tools="shared")
        self.assertEqual(target.read_bytes(), b"another process created this")

    def test_update_preserves_existing_edit_between_plan_and_capture(self):
        self.run_project("install", True, tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        (self.source / "skills/trace/SKILL.md").write_bytes(target.read_bytes() + b" source update")
        manifest = self.root / ".agf/manifest.json"
        original_manifest = manifest.read_bytes()
        original = manage._plan
        def concurrent_edit(*args):
            plan = original(*args)
            target.write_bytes(b"user edit before capture")
            return plan
        with patch.object(manage, "_plan", side_effect=concurrent_edit):
            with self.assertRaisesRegex(AgfError, "Project changed after planning"):
                self.run_project("update", True, tools="shared")
        self.assertEqual(target.read_bytes(), b"user edit before capture")
        self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_rollback_preserves_edit_between_drift_check_and_capture(self):
        self.run_project("install", True, tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        (self.source / "skills/trace/SKILL.md").write_bytes(target.read_bytes() + b" updated")
        self.run_project("update", True, tools="shared")
        manifest = self.root / ".agf/manifest.json"
        original_manifest = manifest.read_bytes()
        original = manage.digest
        def concurrent_edit(path):
            result = original(path)
            if path.name == "manifest.json":
                target.write_bytes(b"new user data")
            return result
        with patch.object(manage, "digest", side_effect=concurrent_edit):
            with self.assertRaisesRegex(AgfError, "changed during rollback"):
                self.run_project("rollback", True, tools="shared")
        self.assertEqual(target.read_bytes(), b"new user data")
        self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_recovery_preserves_edit_to_our_prior_write(self):
        self.run_project("install", True, tools="shared")
        first = self.root / ".agents/skills/trace/SKILL.md"
        second = self.root / ".agf/managed/guides/tools.md"
        (self.source / "skills/trace/SKILL.md").write_bytes(first.read_bytes() + b" source update")
        (self.source / "docs/tools.md").write_bytes(second.read_bytes() + b" source update")
        manifest = self.root / ".agf/manifest.json"
        manifest_before = manifest.read_bytes()
        original = manage._write_checked
        def edit_after_first(root, name, expected, data, touched):
            result = original(root, name, expected, data, touched)
            if name == ".agents/skills/trace/SKILL.md" and data and data.endswith(b" source update"):
                first.write_bytes(b"user edit of updated skill")
                second.write_bytes(b"user edit of later guide")
            return result
        with patch.object(manage, "_write_checked", side_effect=edit_after_first):
            with self.assertRaisesRegex(AgfError, "recovery incomplete"):
                self.run_project("update", True, tools="shared")
        self.assertEqual(first.read_bytes(), b"user edit of updated skill")
        self.assertEqual(second.read_bytes(), b"user edit of later guide")
        self.assertEqual(manifest.read_bytes(), manifest_before)
        self.assertTrue(list((self.root / ".agf/history").glob("*.json")))

    def test_rollback_reverts_its_own_write_and_preserves_later_edit(self):
        self.run_project("install", True, tools="shared")
        first = self.root / ".agents/skills/trace/SKILL.md"
        second = self.root / ".agf/managed/guides/tools.md"
        first_before = first.read_bytes()
        (self.source / "skills/trace/SKILL.md").write_bytes(first_before + b" updated")
        (self.source / "docs/tools.md").write_bytes(second.read_bytes() + b" updated")
        self.run_project("update", True, tools="shared")
        updated_first = first.read_bytes()
        manifest = self.root / ".agf/manifest.json"
        manifest_before = manifest.read_bytes()
        original = manage._write_checked
        def edit_after_restore(root, name, expected, data, touched):
            result = original(root, name, expected, data, touched)
            if name == ".agents/skills/trace/SKILL.md" and data == first_before:
                second.write_bytes(b"user edit during rollback")
            return result
        with patch.object(manage, "_write_checked", side_effect=edit_after_restore):
            with self.assertRaisesRegex(AgfError, "changed during operation"):
                self.run_project("rollback", True, tools="shared")
        self.assertEqual(first.read_bytes(), updated_first)
        self.assertEqual(second.read_bytes(), b"user edit during rollback")
        self.assertEqual(manifest.read_bytes(), manifest_before)

    def test_update_does_not_replace_concurrent_manifest(self):
        self.run_project("install", True, tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        prior = target.read_bytes()
        (self.source / "skills/trace/SKILL.md").write_bytes(prior + b" source update")
        manifest = self.root / ".agf/manifest.json"
        original = manage._write_checked
        def concurrent_manifest(root, name, expected, data, touched):
            if name == manage.MANIFEST:
                manifest.write_bytes(b"another process updated manifest")
            return original(root, name, expected, data, touched)
        with patch.object(manage, "_write_checked", side_effect=concurrent_manifest):
            with self.assertRaisesRegex(AgfError, "changed during operation"):
                self.run_project("update", True, tools="shared")
        self.assertEqual(manifest.read_bytes(), b"another process updated manifest")
        self.assertEqual(target.read_bytes(), prior)

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits only")
    def test_new_state_directory_is_private_without_changing_existing_permissions(self):
        self.run_project("install", True, tools="shared")
        self.assertEqual((self.root / ".agf").stat().st_mode & 0o077, 0)
        other = self.root.parent / (self.root.name + "-existing")
        other.mkdir()
        self.addCleanup(shutil.rmtree, other)
        state = other / ".agf"
        state.mkdir(mode=0o755)
        state.chmod(0o755)
        manage.project(argparse.Namespace(operation="install", target=str(other), source=str(self.source), host=["opencode"], skill=[], tools="shared", apply=True))
        self.assertEqual(state.stat().st_mode & 0o777, 0o755)
        self.assertEqual((state / "history").stat().st_mode & 0o077, 0)
        self.assertEqual((state / "manifest.json").stat().st_mode & 0o077, 0)

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits only")
    def test_existing_public_state_and_history_keep_modes_but_new_files_are_private(self):
        state = self.root / ".agf"
        history = state / "history"
        history.mkdir(parents=True)
        state.chmod(0o755)
        history.chmod(0o755)
        self.run_project("install", True, tools="shared")
        self.assertEqual(state.stat().st_mode & 0o777, 0o755)
        self.assertEqual(history.stat().st_mode & 0o777, 0o755)
        self.assertEqual((state / "manifest.json").stat().st_mode & 0o077, 0)
        for path in (state / "managed").rglob("*"):
            if path.is_file():
                self.assertEqual(path.stat().st_mode & 0o077, 0, str(path))
        snapshots = list(history.glob("*.json"))
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0].stat().st_mode & 0o077, 0)

    def test_snapshot_collision_preserves_existing_file(self):
        history = self.root / ".agf/history"
        history.mkdir(parents=True)
        snapshot = history / "existing.json"
        snapshot.write_bytes(b"other process")
        with self.assertRaises(AgfError):
            manage._write_snapshot(self.root, snapshot, "our snapshot")
        self.assertEqual(snapshot.read_bytes(), b"other process")

    @unittest.skipUnless(os.name == "posix", "POSIX descriptor path only")
    def test_snapshot_fdopen_failure_closes_fd_without_removing_file(self):
        snapshot = self.root / ".agf/history/new.json"
        descriptors = []
        original_open = os.open
        def open_and_record(*args, **kwargs):
            descriptor = original_open(*args, **kwargs)
            descriptors.append(descriptor)
            return descriptor
        with patch.object(manage.os, "open", side_effect=open_and_record), patch.object(manage.os, "fdopen", side_effect=OSError("injected failure")):
            with self.assertRaisesRegex(AgfError, "inspect any partial snapshot"):
                manage._write_snapshot(self.root, snapshot, "payload")
        self.assertEqual(len(descriptors), 1)
        with self.assertRaises(OSError):
            os.fstat(descriptors[0])
        self.assertTrue(snapshot.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits only")
    def test_replace_writes_private_temporary_file_and_retains_target_mode(self):
        target = self.root / "file.txt"
        target.write_bytes(b"old")
        target.chmod(0o640)
        modes = []
        original = os.fchmod
        def observe_mode(descriptor, mode):
            modes.append((os.fstat(descriptor).st_mode & 0o777, mode))
            return original(descriptor, mode)
        with patch.object(manage.os, "fchmod", side_effect=observe_mode):
            manage._replace_bytes(target, b"new")
        self.assertEqual(modes, [(0o600, 0o640)])
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
        self.assertEqual(target.read_bytes(), b"new")

    @unittest.skipUnless(os.name == "posix", "POSIX permission bits only")
    def test_update_and_rollback_preserve_private_managed_file_mode(self):
        self.run_project("install", True, tools="shared")
        target = self.root / ".agents/skills/trace/SKILL.md"
        target.chmod(0o600)
        source = self.source / "skills/trace/SKILL.md"
        source.write_bytes(source.read_bytes() + b" update")
        self.run_project("update", True, tools="shared")
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.run_project("rollback", True, tools="shared")
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_existing_temporary_collision_is_never_deleted(self):
        target = self.root / "file.txt"
        target.write_bytes(b"original")
        fake_id = type("FakeId", (), {"hex": "0" * 32})()
        temporary = target.with_name(target.name + ".agf-" + fake_id.hex + ".tmp")
        temporary.write_bytes(b"other process data")
        with patch.object(manage.uuid, "uuid4", return_value=fake_id):
            with self.assertRaises(FileExistsError):
                manage._replace_bytes(target, b"updated")
        self.assertEqual(temporary.read_bytes(), b"other process data")
        self.assertEqual(target.read_bytes(), b"original")

    @unittest.skipUnless(os.name == "posix", "POSIX descriptor path only")
    def test_fdopen_failure_closes_descriptor_and_preserves_target(self):
        target = self.root / "file.txt"
        target.write_bytes(b"original")
        descriptors = []
        original_open = os.open
        def open_and_record(*args, **kwargs):
            descriptor = original_open(*args, **kwargs)
            descriptors.append(descriptor)
            return descriptor
        with patch.object(manage.os, "open", side_effect=open_and_record), patch.object(manage.os, "fdopen", side_effect=OSError("injected fdopen failure")):
            with self.assertRaisesRegex(OSError, "injected fdopen failure"):
                manage._replace_bytes(target, b"updated")
        self.assertEqual(len(descriptors), 1)
        with self.assertRaises(OSError):
            os.fstat(descriptors[0])
        self.assertEqual(target.read_bytes(), b"original")
        self.assertEqual(list(self.root.glob("file.txt.agf-*.tmp")), [])

    @unittest.skipUnless(os.name == "posix", "Replace an open file only on POSIX")
    def test_failed_temporary_open_preserves_replacement_by_other_process(self):
        target = self.root / "file.txt"
        target.write_bytes(b"original")
        fake_id = type("FakeId", (), {"hex": "1" * 32})()
        temporary = target.with_name(target.name + ".agf-" + fake_id.hex + ".tmp")
        other = self.root / "competitor.txt"
        other.write_bytes(b"other process")
        def replace_then_fail(*args, **kwargs):
            os.replace(other, temporary)
            raise OSError("injected failure")
        with patch.object(manage.uuid, "uuid4", return_value=fake_id), patch.object(manage.os, "fdopen", side_effect=replace_then_fail):
            with self.assertRaises(OSError):
                manage._replace_bytes(target, b"updated")
        self.assertEqual(temporary.read_bytes(), b"other process")
        self.assertEqual(target.read_bytes(), b"original")

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
        self.assertEqual(len(value["files"]), 2 + len(manage.GUIDES) + 1, "rules, agf-cli.md (S20), guides, AGENTS.md")
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".agf/managed/runtime").exists())
        self.assertFalse((self.root / ".agf/managed/profile.example.json").exists())
        self.assertIn(str(self.source / "scripts/agf.py"), (self.root / ".agf/managed/agf-cli.md").read_text(encoding="utf-8"))
        rules = (self.root / ".agf/managed/project-rules.md").read_text(encoding="utf-8")
        self.assertNotIn(str(self.source / "scripts/agf.py"), rules, "the path is read on demand (S20)")
        self.assertIn("`.agf/managed/agf-cli.md`", rules)

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
            def fileno(self):
                return self.stream.fileno()

        original_create = manage._open_create
        def open_file(path, private):
            stream = original_create(path, private)
            return BrokenWrite(stream) if path == destination else stream

        with patch.object(manage, "_open_create", side_effect=open_file):
            with self.assertRaises(AgfError):
                self.run_project("install", True, tools="shared")
        self.assertFalse(destination.exists())
        self.assertFalse((self.root / ".agf/manifest.json").exists())
        self.assertEqual(notes.read_text(encoding="utf-8"), "User content")

    @unittest.skipUnless(os.name == "posix", "Replace an open file only on POSIX")
    def test_partial_create_replaced_by_equal_prefix_is_preserved(self):
        destination = self.root / ".agf/managed/project-rules.md"
        original_create = manage._open_create
        observed = []
        class ReplacedWrite:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def fileno(self):
                return self.stream.fileno()
            def write(self, data):
                prefix = data[:3]
                self.stream.write(prefix)
                self.stream.flush()
                other = destination.with_name("other-file")
                other.write_bytes(prefix)
                os.replace(other, destination)
                observed.append(prefix)
                raise OSError("injected failure after another process replaced path")
        def open_file(path, private):
            stream = original_create(path, private)
            return ReplacedWrite(stream) if path == destination else stream
        with patch.object(manage, "_open_create", side_effect=open_file):
            with self.assertRaisesRegex(AgfError, "recovery incomplete"):
                self.run_project("install", True, tools="shared")
        self.assertEqual(destination.read_bytes(), observed[0])
        self.assertFalse((self.root / ".agf/manifest.json").exists())

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

    def use_real_rules(self):
        shutil.copyfile(manage.SOURCE / "templates/project-rules.md", self.source / "templates/project-rules.md")
        return self.root / ".agf/managed/project-rules.md"

    def test_the_real_template_has_one_skill_rule_to_make_conditional(self):
        lines = (manage.SOURCE / "templates/project-rules.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(line.startswith("- **skill。**") for line in lines), 1)

    def test_the_skill_rule_follows_the_skills_that_end_up_installed(self):
        rules = self.use_real_rules()
        present = lambda: "**skill。**" in rules.read_text(encoding="utf-8")
        self.run_project("install", True, skills=[])
        self.assertFalse(present())
        for kept in ("**對齊。**", "**驗證。**", "**Git 與授權。**", "practices.md"):
            self.assertIn(kept, rules.read_text(encoding="utf-8"))
        self.run_project("update", True, skills=["trace"])
        self.assertTrue(present())
        self.run_project("rollback", True)
        self.assertFalse(present())

    def test_an_update_that_preserves_skills_keeps_the_skill_rule(self):
        rules = self.use_real_rules()
        self.run_project("install", True, skills=["trace"])
        self.run_project("update", True, skills=[])  # nothing refreshed, trace stays installed
        self.assertTrue((self.root / ".agents/skills/trace/SKILL.md").is_file())
        self.assertIn("**skill。**", rules.read_text(encoding="utf-8"))
        shutil.rmtree(self.source / "skills/trace")
        (self.source / "skills").mkdir(exist_ok=True)
        self.run_project("update", True, skills=[])
        self.assertFalse((self.root / ".agents/skills/trace/SKILL.md").exists())
        self.assertNotIn("**skill。**", rules.read_text(encoding="utf-8"))

    def test_the_cli_note_follows_the_tools_mode_and_never_overwrites_a_users_file(self):
        note = self.root / ".agf/managed/agf-cli.md"
        note.parent.mkdir(parents=True)
        note.write_text("mine", encoding="utf-8")
        with self.assertRaises(AgfError):
            self.run_project("install", True)
        self.assertEqual(note.read_text(encoding="utf-8"), "mine")
        note.unlink()
        self.run_project("install", True, tools="shared")
        self.assertIn("`shared`", note.read_text(encoding="utf-8"))
        self.run_project("update", True, tools="copy")
        self.assertIn(".agf/managed/runtime/scripts/agf.py", note.read_text(encoding="utf-8"))
        self.run_project("rollback", True)
        self.assertIn("`shared`", note.read_text(encoding="utf-8"))

    def test_writing_a_document_still_reaches_the_rules_only_practices_has(self):
        # S20 P5 dropped this trigger and was reverted: these two rules live nowhere else.
        read = lambda name: (manage.SOURCE / name).read_text(encoding="utf-8")
        self.assertIn("寫交接檔或文件之前，先讀 `.agf/managed/guides/practices.md`", read("templates/project-rules.md"))
        for kept in ("agf profile show", "以執行結果與目前的原始碼為準"):
            self.assertIn(kept, read("docs/practices.md"))

    def test_both_writing_guides_state_the_rewriting_rule_in_the_same_words(self):
        # A rule buried mid-paragraph scored lower on fidelity (S19, S21): it stands alone in both guides.
        lines = {name: [line.removeprefix("- ") for line in (manage.SOURCE / name).read_text(encoding="utf-8").splitlines()
                        if line.removeprefix("- ").startswith("**改寫只用原稿的事實。**")]
                 for name in ("docs/writing.md", "docs/writing-short.md")}
        self.assertEqual(len(lines["docs/writing.md"]), 1)
        self.assertEqual(lines["docs/writing.md"], lines["docs/writing-short.md"])

    def test_deployed_text_points_at_the_cli_note_for_the_path(self):
        for name in ("docs/tools.md", "docs/writing.md", "docs/cli.md", "templates/diagrams/README.md"):
            text = (manage.SOURCE / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"規則所列|專案規則的 CLI|project-rules\.md` 的 CLI", name)
            self.assertIn("agf-cli.md", text, name)

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
