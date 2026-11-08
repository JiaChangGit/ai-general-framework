import argparse
import hashlib
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agf import sources
from agf.common import AgfError


def invoke(*argv):
    parser = argparse.ArgumentParser()
    sources.register(parser.add_subparsers(required=True))
    args = parser.parse_args(argv)
    return args.func(args)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agf-source-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def make(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def test_text_hash_and_physical_line_anchors(self):
        path = self.make("中文.txt", "first\n\n第三行\n")
        result = sources.load_source(path)
        self.assertEqual(result["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(result["entries"][2]["anchor"], "line:3")
        excerpt = invoke("source", "excerpt", str(path), "--query", "第三")
        self.assertEqual(excerpt["excerpts"][0]["line"], 3)

    def test_text_unit_limit_rejects_before_splitlines_for_inspect_and_excerpt(self):
        path = self.make("many.txt", "one\n\ntwo\nthree\n")
        with patch.object(sources, "MAX_SOURCE_UNITS", 3):
            for operation in ("inspect", "excerpt"):
                with self.subTest(operation=operation), self.assertRaisesRegex(AgfError, "exceeds 3 lines"):
                    invoke("source", operation, str(path))
            path.write_text("one\n\ntwo\n", encoding="utf-8")
            result = invoke("source", "excerpt", str(path))
            self.assertEqual([unit["anchor"] for unit in result["excerpts"]], ["line:1", "line:3"])

    def test_unicode_line_breaks_match_splitlines_limit(self):
        with patch.object(sources, "MAX_SOURCE_UNITS", 2):
            for content in ("a\r\nb\r\nc", "a\vb\vc", "a\x85b\x85c", "a\u2028b\u2028c"):
                with self.subTest(content=repr(content)), self.assertRaisesRegex(AgfError, "exceeds 2 lines"):
                    sources._check_line_count(content)
            sources._check_line_count("a\r\nb\r\n")

    def test_html_many_fragments_on_one_line_and_encoded_breaks_are_bounded(self):
        path = self.make("many.html", "<b>x</b>" * 4)
        with patch.object(sources, "MAX_SOURCE_UNITS", 3):
            with self.assertRaisesRegex(AgfError, "exceeds 3 text units"):
                invoke("source", "inspect", str(path))
            path.write_text("<p>a&#10;b&#10;c&#10;d</p>", encoding="utf-8")
            with self.assertRaisesRegex(AgfError, "exceeds 3 lines"):
                invoke("source", "excerpt", str(path))

    def test_oversized_text_rejected_before_hashing(self):
        path = self.make("oversized.txt", "abc")
        with patch.object(sources, "MAX_TEXT_BYTES", 2), patch.object(sources, "_hash") as hash_file:
            with self.assertRaisesRegex(AgfError, "exceeds 50 MB"):
                sources.load_source(path)
            hash_file.assert_not_called()

    def test_excerpt_has_total_not_per_unit_budget(self):
        path = self.make("many.txt", "1234567890\nABCDEFGHIJ\nlast\n")
        result = invoke("source", "excerpt", str(path), "--max-chars", "12", "--limit", "3")
        self.assertEqual(sum(len(e["text"]) for e in result["excerpts"]), 12)
        self.assertTrue(result["truncated"])

    def test_line_selectors_and_no_match(self):
        path = self.make("lines.md", "one\ntwo\nthree")
        result = invoke("source", "excerpt", str(path), "--start-line", "2", "--end-line", "2")
        self.assertEqual([e["text"] for e in result["excerpts"]], ["two"])
        self.assertEqual(invoke("source", "excerpt", str(path), "--query", "absent")["matches"], 0)
        with self.assertRaises(AgfError):
            invoke("source", "excerpt", str(path), "--pages", "1")

    def test_static_html_preserves_original_lines_without_executing_scripts(self):
        path = self.make("page.html", '<h1>Title &amp; text</h1>\n<script>steal()</script>\n<style>bad</style>\n<p>第三行內容</p>')
        result = sources.load_source(path)
        text = " ".join(e["text"] for e in result["entries"])
        self.assertIn("Title & text", text)
        self.assertNotIn("steal", text)
        self.assertNotIn("bad", text)
        self.assertEqual(result["entries"][-1]["line"], 4)

    def test_missing_optional_pdf_dependency_is_unavailable(self):
        path = self.make("paper.pdf", "%PDF fake fixture")
        with patch.dict(sys.modules, {"pypdf": None}):
            result = invoke("source", "inspect", str(path))
        self.assertEqual(result["status"], "UNAVAILABLE")
        self.assertIn("pypdf", result["detail"])

    def test_pdf_page_numbers_and_selection_using_adapter_fixture(self):
        path = self.make("paper.pdf", "%PDF adapter fixture")
        reader = SimpleNamespace(is_encrypted=False, pages=[SimpleNamespace(extract_text=lambda: "first page"), SimpleNamespace(extract_text=lambda: "second page")])
        with patch.dict(sys.modules, {"pypdf": SimpleNamespace(PdfReader=lambda _: reader)}):
            result = invoke("source", "excerpt", str(path), "--pages", "2")
        self.assertEqual(result["excerpts"][0]["anchor"], "page:2")
        self.assertIn("physical", result["anchor_basis"])

    def test_pdf_unit_and_extracted_text_limits(self):
        path = self.make("paper.pdf", "%PDF adapter fixture")
        pages = [SimpleNamespace(extract_text=lambda: "abc") for _ in range(4)]
        reader = SimpleNamespace(is_encrypted=False, pages=pages)
        with patch.dict(sys.modules, {"pypdf": SimpleNamespace(PdfReader=lambda _: reader)}), patch.object(sources, "MAX_SOURCE_UNITS", 3):
            with self.assertRaisesRegex(AgfError, "exceeds 3 pages"):
                invoke("source", "inspect", str(path))
            with self.assertRaisesRegex(AgfError, "exceeds 3 pages"):
                invoke("source", "excerpt", str(path), "--pages", "1-4")
            result = invoke("source", "excerpt", str(path), "--pages", "4")
            self.assertEqual(result["excerpts"][0]["anchor"], "page:4")
            with patch.object(sources, "MAX_PDF_TEXT_CHARS", 5):
                with self.assertRaisesRegex(AgfError, "extracted text exceeds 5 characters"):
                    invoke("source", "excerpt", str(path), "--pages", "1-2")

    def test_pdf_inspection_does_not_extract_page_text(self):
        path = self.make("paper.pdf", "%PDF adapter fixture")
        def expensive():
            raise AssertionError("Metadata inspection must not extract page text")
        reader = SimpleNamespace(is_encrypted=False, pages=[SimpleNamespace(extract_text=expensive)])
        with patch.dict(sys.modules, {"pypdf": SimpleNamespace(PdfReader=lambda _: reader)}):
            result = invoke("source", "inspect", str(path))
        self.assertEqual(result["units"], 1)
        self.assertFalse(result["text_extracted"])
        self.assertIsNone(result["empty_units"])

    def test_unselected_pdf_pages_are_not_extracted(self):
        path = self.make("paper.pdf", "%PDF adapter fixture")
        def unselected():
            raise AssertionError("Unselected page must not be extracted")
        reader = SimpleNamespace(is_encrypted=False, pages=[SimpleNamespace(extract_text=unselected), SimpleNamespace(extract_text=lambda: "selected")])
        with patch.dict(sys.modules, {"pypdf": SimpleNamespace(PdfReader=lambda _: reader)}):
            result = invoke("source", "excerpt", str(path), "--pages", "2")
        self.assertEqual(result["excerpts"][0]["anchor"], "page:2")
        self.assertEqual(result["total_units"], 2)

    def test_encrypted_pdf_is_not_treated_as_success(self):
        path = self.make("encrypted.pdf", "%PDF fixture")
        with patch.dict(sys.modules, {"pypdf": SimpleNamespace(PdfReader=lambda _: SimpleNamespace(is_encrypted=True))}):
            with self.assertRaisesRegex(AgfError, "Encrypted"):
                invoke("source", "inspect", str(path))

    def test_diff_candidates_have_hashes_and_bounded_excerpts(self):
        before = self.make("before.md", "same\nold requirement\n")
        after = self.make("after.md", "same\nnew requirement\n")
        result = invoke("source", "diff", str(before), str(after), "--max-chars", "10")
        self.assertEqual(result["status"], "CANDIDATE_DIFF")
        self.assertEqual(result["changes"][0]["before_anchors"], ["line:2"])
        self.assertEqual(len(result["before"]["sha256"]), 64)
        self.assertLessEqual(sum(len(c["before"]) + len(c["after"]) for c in result["changes"]), 10)
        self.assertTrue(result["truncated"])

    def test_invalid_encoding_and_limits_are_actionable(self):
        path = self.root / "bad.txt"
        path.write_bytes(b"\xff")
        with self.assertRaisesRegex(AgfError, "UTF-8"):
            invoke("source", "inspect", str(path))
        path.write_text("fine")
        with self.assertRaises(AgfError):
            invoke("source", "excerpt", str(path), "--max-chars", "0")


if __name__ == "__main__":
    unittest.main()
