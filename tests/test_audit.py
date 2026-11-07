from pathlib import Path
import tempfile
import unittest

from agf.audit import audit


class AuditTests(unittest.TestCase):
    def test_broken_link_and_syntax_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo\ndescription: Demo workflow.\n---\n[Missing](references/missing.md)\n")
            package = root / "agf"
            package.mkdir()
            (package / "broken.py").write_text("def broken(\n")
            result = audit(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(len(result["errors"]), 2)

    def test_empty_collection_does_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(audit(temp)["status"], "FAIL")

    def test_ambiguous_yaml_description_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skills" / "demo" / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text("---\nname: demo\ndescription: Do this: then that\n---\nBody\n")
            self.assertEqual(audit(temp)["status"], "FAIL")
            path.write_text('---\nname: demo\ndescription: "Do this: then that"\n---\nBody\n')
            self.assertEqual(audit(temp)["status"], "PASS")

    def test_supporting_document_links_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "demo" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: demo\ndescription: Demo.\n---\nBody\n")
            (root / "README.md").write_text("[Usage](docs/missing.md)\n")
            self.assertEqual(audit(root)["status"], "FAIL")
