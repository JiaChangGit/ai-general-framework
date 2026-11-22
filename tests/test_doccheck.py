from pathlib import Path
import tempfile
import unittest

from agf import doccheck


class DocCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "agf").mkdir()
        (self.root / "agf" / "cli.py").write_text("# marker\n", encoding="utf-8")
        (self.root / "templates").mkdir()
        (self.root / "templates" / "spec.md").write_text("# spec\n", encoding="utf-8")
        (self.root / "docs" / "ecosystem").mkdir(parents=True)

    def write(self, name, text):
        path = self.root / "docs" / name
        path.write_text(text, encoding="utf-8")

    def test_names_that_exist_pass(self):
        self.write("guide.md", "Run `agf traces check --target .` or\n\n```console\npython scripts/agf.py audit --root .\n"
                               "python scripts/agf.py project install --target x --keep-ai-traces --apply\n```\n\nSee `templates/spec.md`.\n")
        self.assertEqual(doccheck.check(self.root), [])

    def test_stale_commands_options_and_paths_are_reported(self):
        self.write("guide.md", "`agf traces scan`\n\n`agf audit --config x`\n\n`agf frobnicate`\n\n`templates/missing.md`\n\n`docs/ecosystem/gone.md`\n")
        problems = "\n".join(doccheck.check(self.root))
        for expected in ("docs/guide.md:1: `agf traces` has no operation `scan`", "has no option `--config`",
                         "no subcommand `frobnicate`", "path `templates/missing.md`", "path `docs/ecosystem/gone.md`"):
            self.assertIn(expected, problems)

    def test_stale_top_level_docs_and_continued_commands_are_reported(self):
        self.write("guide.md", "See `docs/old-name.md`.\n\n```bash\npython scripts/agf.py audit \\\n  --nonexistent\n```\n")
        problems = "\n".join(doccheck.check(self.root))
        self.assertIn("path `docs/old-name.md`", problems)
        self.assertIn("has no option `--nonexistent`", problems)

    def test_project_paths_and_dated_records_are_not_checked(self):
        self.write("guide.md", "A project may keep `docs/HANDOFF.md` or `skills/its-own-skill/`.\n")
        self.write("analysis-2026-11.md", "Back then we proposed `agf task record --checkpoint`.\n")
        self.assertEqual(doccheck.check(self.root), [])


if __name__ == "__main__":
    unittest.main()
