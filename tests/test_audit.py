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

    def test_nested_template_reference_is_checked_and_can_be_repaired(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "skills" / "demo" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: demo\ndescription: Demo.\n---\nBody\n", encoding="utf-8")
            guide = root / "templates" / "presentations" / "README.md"
            guide.parent.mkdir(parents=True)
            guide.write_text(
                "[Diagram guide](../diagrams/README.md#usage)\n"
                "[Web](https://example.invalid/docs) [HTTP](http://example.invalid/docs)\n"
                "[This section](#usage) [Contact](mailto:test@example.invalid)\n",
                encoding="utf-8",
            )

            result = audit(root)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["errors"], [f"{guide.resolve()}: missing linked file ../diagrams/README.md"])
            self.assertEqual(result["_exit_code"], 1)

            reference = root / "templates" / "diagrams" / "README.md"
            reference.parent.mkdir()
            reference.write_text("# Usage\n", encoding="utf-8")
            repaired = audit(root)
            self.assertEqual(repaired["status"], "PASS")
            self.assertEqual(repaired["errors"], [])
            self.assertEqual(repaired["_exit_code"], 0)
