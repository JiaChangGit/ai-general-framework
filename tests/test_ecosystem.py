import json
from pathlib import Path
import tempfile
import unittest

from agf import ecosystem


def entry(**changes):
    value = {
        "id": "demo-tool", "name": "Demo", "category": "shell-utilities", "type": "cli",
        "urls": {"source": "https://github.com/example/demo"}, "summary": "示範用的工具。",
        "license": {"spdx": "MIT", "label": "usable"}, "tier": 2, "evidence": "docs", "confidence": "medium",
        "checked": "2026-11-21", "references": [{"url": "https://github.com/example/demo", "level": "READ"}],
    }
    value.update(changes)
    return value


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        folder = self.root / "docs" / "ecosystem"
        (folder / "categories").mkdir(parents=True)
        (folder / "README.md").write_text("# 索引\n\n<!-- ecosystem:index -->\n<!-- /ecosystem -->\n\n<!-- ecosystem:tier1 -->\n<!-- /ecosystem -->\n", encoding="utf-8")
        (folder / "categories" / "shell-utilities.md").write_text("# Shell\n\n<!-- ecosystem:table shell-utilities -->\n<!-- /ecosystem -->\n", encoding="utf-8")
        self.write([entry()])

    def tearDown(self):
        self.temp.cleanup()

    def write(self, entries):
        data = {"schema": 1, "categories": {"shell-utilities": {"title": "Shell 工具", "page": "categories/shell-utilities.md"}},
                "entries": entries}
        (self.root / "docs" / "ecosystem" / "entries.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_missing_catalog_is_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(ecosystem.check(temp)["status"], "SKIPPED")

    def test_stale_table_fails_until_rendered(self):
        result = ecosystem.check(self.root)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("out of date", result["errors"][0])
        self.assertEqual(len(ecosystem.render(self.root)["changed"]), 2)
        self.assertEqual(ecosystem.check(self.root)["status"], "PASS")
        page = (self.root / "docs" / "ecosystem" / "categories" / "shell-utilities.md").read_text(encoding="utf-8")
        self.assertIn("[Demo](https://github.com/example/demo) | CLI | 2 | 可使用（MIT）", page)

    def test_invalid_fields_are_reported(self):
        self.write([entry(category="nope"), entry(id="Bad_ID", tier=7, license={"label": "maybe"}, alternatives=["ghost"])])
        errors = ecosystem.check(self.root)["errors"]
        joined = "\n".join(errors)
        for expected in ("unknown category nope", "id must be lowercase", "tier must be 1-4", "license.label", "ghost is not an entry id"):
            self.assertIn(expected, joined)

    def test_duplicate_ids_and_missing_fields_fail(self):
        self.write([entry(), entry(), entry(id="other", summary="")])
        errors = "\n".join(ecosystem.check(self.root)["errors"])
        self.assertIn("duplicate id demo-tool", errors)
        self.assertIn("other: missing summary", errors)

    def test_record_references_must_be_relative_and_exist(self):
        (self.root / "docs" / "old-study.md").write_text("# 舊紀錄\n", encoding="utf-8")
        good = {"path": "docs/old-study.md", "level": "RECORD"}
        self.write([entry(references=[good])])
        ecosystem.render(self.root)
        self.assertEqual(ecosystem.check(self.root)["status"], "PASS")
        for bad, message in (({"path": "/abs/old-study.md", "level": "RECORD"}, "relative to the framework root"),
                             ({"path": "docs/../docs/old-study.md", "level": "RECORD"}, "relative to the framework root"),
                             ({"path": "docs/old-study.md", "level": "READ"}, "level RECORD"),
                             ({"path": "docs/missing.md", "level": "RECORD"}, "does not exist")):
            self.write([entry(references=[bad])])
            self.assertIn(message, "\n".join(ecosystem.check(self.root)["errors"]), bad)

    def test_pipes_in_text_do_not_break_the_table(self):
        self.write([entry(summary="a | b")])
        ecosystem.render(self.root)
        page = (self.root / "docs" / "ecosystem" / "categories" / "shell-utilities.md").read_text(encoding="utf-8")
        self.assertIn("a \\| b", page)

    def test_refresh_stores_facts_and_reports_failures(self):
        self.write([entry(), entry(id="no-repo", urls={"official": "https://example.org"}), entry(id="broken", urls={"source": "https://github.com/example/broken"})])
        calls = []

        def runner(arguments):
            calls.append(arguments[1])
            if "broken" in arguments[1]:
                raise ecosystem.AgfError("HTTP 404")
            return {"full_name": "example/demo", "pushed_at": "2026-10-01T00:00:00Z", "archived": False, "stars": 5, "license": "MIT"}

        result = ecosystem.refresh(self.root, runner=runner, today="2026-11-21")
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(calls, ["repos/example/demo", "repos/example/broken"])
        data = ecosystem.load(self.root)
        self.assertEqual(data["entries"][0]["github"]["fetched"], "2026-11-21")
        self.assertNotIn("github", data["entries"][1])
        ecosystem.render(self.root)
        page = (self.root / "docs" / "ecosystem" / "categories" / "shell-utilities.md").read_text(encoding="utf-8")
        self.assertIn("| 2026-10-01 |", page)

    def test_find_is_bounded_and_requires_every_term(self):
        self.write([entry(), entry(id="pdf-tool", name="PDF Tool", summary="解析 PDF 表格。"), entry(id="pdf-other", name="Other", summary="PDF 轉 Markdown。")])
        result = ecosystem.find(self.root, ["pdf", "表格"], limit=5)
        self.assertEqual([r["id"] for r in result["results"]], ["pdf-tool"])
        self.assertEqual(ecosystem.find(self.root, ["pdf"], limit=1)["shown"], 1)


if __name__ == "__main__":
    unittest.main()
