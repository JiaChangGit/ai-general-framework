import argparse
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from agf import files
from agf.common import AgfError


def invoke(*argv):
    parser = argparse.ArgumentParser()
    files.register(parser.add_subparsers(required=True))
    args = parser.parse_args(argv)
    return args.func(args)


class FileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agf-files-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "中文 space"
        self.root.mkdir()

    def make(self, name, content=b"original"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_rename_preview_is_read_only_and_plan_applies(self):
        source = self.make("Old.txt")
        result = invoke("files", "rename", str(self.root), "--pattern", "Old", "--replace", "New")
        self.assertEqual(result["status"], "PLAN")
        self.assertEqual([p.name for p in self.root.iterdir()], ["Old.txt"])
        self.assertEqual(files.apply_plan(result["plan"])["changed"], 1)
        self.assertFalse(source.exists())
        self.assertEqual((self.root / "New.txt").read_bytes(), b"original")

    def test_source_drift_refuses_whole_batch(self):
        first = self.make("old1")
        self.make("old2")
        plan = files.rename_plan(self.root, "old", "new")
        first.write_bytes(b"changed")
        with self.assertRaises(AgfError):
            files.apply_plan(plan)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["old1", "old2"])

    def test_case_collision_is_refused_before_writes(self):
        self.make("a.txt")
        self.make("B.txt")
        with self.assertRaises(AgfError):
            files.rename_plan(self.root, "^a", "b")
        self.assertTrue((self.root / "a.txt").exists())

    def test_case_only_rename(self):
        self.make("UP.txt")
        files.apply_plan(files.rename_plan(self.root, "UP", "up"))
        self.assertIn("up.txt", [p.name for p in self.root.iterdir()])

    def test_swap_uses_original_backups(self):
        self.make("a", b"A")
        self.make("b", b"B")
        plan = {"schema": 1, "kind": "rename", "root": str(self.root), "operations": [
            {"source": "a", "target": "b", "sha256": files._hash(self.root / "a")},
            {"source": "b", "target": "a", "sha256": files._hash(self.root / "b")} ]}
        files.apply_plan(plan)
        self.assertEqual((self.root / "a").read_bytes(), b"B")
        self.assertEqual((self.root / "b").read_bytes(), b"A")

    def test_copy_failure_restores_batch(self):
        self.make("old1", b"one")
        self.make("old2", b"two")
        plan = files.rename_plan(self.root, "old", "new")
        real = shutil.copyfileobj
        calls = 0
        def failing(src, dst):
            nonlocal calls
            calls += 1
            if calls == 2:
                dst.write(b"partial")
                raise OSError("simulated disk error")
            return real(src, dst)
        with patch.object(files.shutil, "copyfileobj", failing):
            with self.assertRaisesRegex(AgfError, "originals restored"):
                files.apply_plan(plan)
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["old1", "old2"])
        self.assertEqual((self.root / "old2").read_bytes(), b"two")

    def test_unsafe_target_and_traversal_refused(self):
        self.make("old.txt")
        for replacement in ("CON", "../escape", "bad:", "bad."):
            with self.subTest(replacement=replacement), self.assertRaises(AgfError):
                files.rename_plan(self.root, "^.*$", replacement)
        plan = files.rename_plan(self.root, "old", "new")
        plan["operations"][0]["target"] = "../escape"
        with self.assertRaises(AgfError):
            files.apply_plan(plan)

    def test_symlink_is_not_followed(self):
        self.make("old.txt")
        try:
            (self.root / "alias").symlink_to(self.root / "old.txt")
        except OSError as exc:
            self.skipTest(f"Host cannot create test symlinks: {exc}")
        with self.assertRaisesRegex(AgfError, "Symlink"):
            files.rename_plan(self.root, "old", "new")

    def test_normalize_preview_apply_and_strict_encoding(self):
        source = self.make("input.txt", "台灣\r\n中文\r".encode("utf-16"))
        plan = files.normalize_plan(self.root, "utf-16", "utf-8", "lf")
        self.assertTrue(source.read_bytes().startswith(b"\xff\xfe"))
        files.apply_plan(plan)
        self.assertEqual(source.read_bytes(), "台灣\n中文\n".encode())
        self.make("broken.txt", b"\xff")
        with self.assertRaises(AgfError):
            files.normalize_plan(self.root, "utf-8", "utf-8", "lf")
        self.assertEqual((self.root / "broken.txt").read_bytes(), b"\xff")

    def test_saved_plan_needs_apply_and_never_overwrites_output(self):
        self.make("old")
        output = Path(self.temp.name) / "plan.json"
        invoke("files", "rename", str(self.root), "--pattern", "old", "--replace", "new", "--plan-output", str(output))
        self.assertEqual(invoke("files", "apply", str(output))["status"], "PLAN")
        self.assertTrue((self.root / "old").exists())
        with self.assertRaises(AgfError):
            invoke("files", "rename", str(self.root), "--pattern", "old", "--replace", "new", "--plan-output", str(output))
        invoke("files", "apply", str(output), "--apply")
        self.assertTrue((self.root / "new").exists())

    def test_saved_plan_ignores_unlisted_files_but_checks_new_collisions(self):
        self.make("old")
        plan_path = self.root / "plan.json"
        invoke("files", "rename", str(self.root), "--pattern", "old", "--replace", "new", "--plan-output", str(plan_path))
        self.make("unlisted", b"do not touch")
        self.make("NEW", b"new collision")
        with self.assertRaisesRegex(AgfError, "collision"):
            invoke("files", "apply", str(plan_path), "--apply")
        (self.root / "NEW").unlink()
        invoke("files", "apply", str(plan_path), "--apply")
        self.assertEqual((self.root / "unlisted").read_bytes(), b"do not touch")
        self.assertTrue(plan_path.is_file())

    def test_json_diff_preserves_types_containers_and_keys(self):
        left = self.make("left.json", json.dumps({"empty": {}, "bool": True, "a/b": {"x.y": 1}}).encode())
        right = self.make("right.json", json.dumps({"empty": [], "bool": 1, "a/b": {"x.y": 2}}).encode())
        result = invoke("files", "diff", str(left), str(right), "--format", "json")
        self.assertEqual({c["path"] for c in result["changes"]}, {"/empty", "/bool", "/a~1b/x.y"})

    def test_folder_diff_and_text_budget(self):
        left, right = self.root / "left", self.root / "right"
        left.mkdir()
        right.mkdir()
        (left / "same").write_bytes(b"same")
        (right / "same").write_bytes(b"same")
        (left / "different").write_bytes(b"one")
        (right / "different").write_bytes(b"two")
        result = invoke("files", "diff", str(left), str(right), "--format", "folder")
        self.assertEqual(result["changed"], ["different"])
        text = invoke("files", "diff", str(left / "different"), str(right / "different"), "--max-chars", "10")
        self.assertTrue(text["truncated"])
        self.assertEqual(len(text["diff"]), 10)


if __name__ == "__main__":
    unittest.main()
