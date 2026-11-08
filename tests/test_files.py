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

    def test_recursive_rename_skips_vcs_metadata_but_keeps_other_hidden_files(self):
        protected = [self.make(f"{directory}/old-data", b"metadata")
                     for directory in (".git", ".SvN", "nested/.HG")]
        ordinary = [self.make("old.txt"), self.make("nested/old.txt"), self.make(".settings/old.txt")]
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        plan = files.rename_plan(self.root, "old", "new", recursive=True)
        self.assertEqual({op["source"] for op in plan["operations"]},
                         {p.relative_to(self.root).as_posix() for p in ordinary})
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        files.apply_plan(plan)
        for path in protected:
            self.assertEqual(path.read_bytes(), b"metadata")
        for path in ordinary:
            self.assertFalse(path.exists())
            self.assertEqual(path.with_name("new.txt").read_bytes(), b"original")

    def test_recursive_normalize_does_not_read_or_change_metadata(self):
        protected = [self.make(f"{directory}/wc.db", b"\xff\x00\r\n")
                     for directory in (".git", ".svn", "nested/.hG")]
        ordinary = [self.make("input.txt", b"text\r\n"), self.make(".hidden/input.txt", b"hidden\r\n")]
        plan = files.normalize_plan(self.root, "utf-8", "utf-8", "lf", recursive=True)
        self.assertEqual({op["source"] for op in plan["operations"]},
                         {p.relative_to(self.root).as_posix() for p in ordinary})
        self.assertEqual([path.read_bytes() for path in ordinary], [b"text\r\n", b"hidden\r\n"])
        files.apply_plan(plan)
        self.assertEqual([path.read_bytes() for path in protected], [b"\xff\x00\r\n"] * 3)
        self.assertEqual([path.read_bytes() for path in ordinary], [b"text\n", b"hidden\n"])

    def test_metadata_marker_files_are_not_renamed(self):
        # Git worktrees can use a .git file instead of a directory.
        markers = [self.make(name, b"metadata marker") for name in (".GiT", ".SVN", ".hg")]
        self.make(".env", b"ordinary hidden file")
        plan = files.rename_plan(self.root, "^", "prefix-")
        self.assertEqual([op["source"] for op in plan["operations"]], [".env"])
        files.apply_plan(plan)
        self.assertTrue((self.root / "prefix-.env").is_file())
        self.assertEqual([path.read_bytes() for path in markers], [b"metadata marker"] * 3)

    def test_saved_plans_cannot_use_metadata_sources_or_targets(self):
        regular = self.make("ordinary.txt", b"ordinary")
        protected = self.make(".SvN/old-data", b"protected")
        cases = [
            {"source": ".SvN/old-data", "target": ".SvN/new-data", "sha256": files._hash(protected)},
            {"source": "ordinary.txt", "target": ".hG", "sha256": files._hash(regular)},
        ]
        for kind in ("rename", "normalize"):
            for index, operation in enumerate(cases):
                with self.subTest(kind=kind, operation=operation):
                    # The first operation is valid; a later forbidden one must
                    # stop the whole plan before any ordinary source is moved.
                    first = {"source": "ordinary.txt", "target": "ordinary.txt" if kind == "normalize" else "renamed.txt",
                             "sha256": files._hash(regular)}
                    plan = {"schema": 1, "kind": kind, "root": str(self.root), "operations": [first, operation],
                            "settings": {"from_encoding": "utf-8", "to_encoding": "utf-8", "newline": "lf"}}
                    saved = Path(self.temp.name) / f"forged-{kind}-{index}.json"
                    saved.write_text(json.dumps(plan), encoding="utf-8")
                    for apply_args in ((), ("--apply",)):
                        with self.assertRaisesRegex(AgfError, "VCS metadata"):
                            invoke("files", "apply", str(saved), *apply_args)
                    self.assertEqual(regular.read_bytes(), b"ordinary")
                    self.assertEqual(protected.read_bytes(), b"protected")
                    self.assertFalse((self.root / "renamed.txt").exists())
                    self.assertFalse(any(self.root.glob(".agf-files-*")))

    def test_metadata_root_or_ancestor_is_refused_even_in_saved_plan(self):
        for directory in (".git", ".sVn", ".HG"):
            source = self.make(f"{directory}/nested/ordinary.txt", b"metadata")
            for root in (source.parent, source.parent.parent):
                with self.subTest(root=root):
                    with self.assertRaisesRegex(AgfError, "VCS metadata"):
                        files.rename_plan(root, "ordinary", "new", recursive=True)
                    with self.assertRaisesRegex(AgfError, "VCS metadata"):
                        files.normalize_plan(root, "utf-8", "utf-8", "lf", recursive=True)
                    # Empty operations do not bypass the root restriction.
                    with self.assertRaisesRegex(AgfError, "VCS metadata"):
                        files.apply_plan({"schema": 1, "kind": "rename", "root": str(root), "operations": []})
            self.assertEqual(source.read_bytes(), b"metadata")

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
