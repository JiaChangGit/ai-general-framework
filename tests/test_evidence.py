import json
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess

from agf.common import AgfError
from agf.evidence import check_task, handoff, record_task


class EvidenceTests(unittest.TestCase):
    def test_changed_evidence_blocks_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.py"
            source.write_text("original\n")
            contract = root / "input.json"
            contract.write_text(json.dumps({"goal": "Find cause", "scope": ["source.py"], "acceptance": ["Reproduce the failure"], "evidence": [{"path": "source.py", "note": "Source inspection only"}]}))
            output = root / "record.json"
            result = record_task(contract, output, root)
            self.assertEqual(result["status"], "RECORDED")
            self.assertIsNone(result["usage"]["tokens"])
            self.assertEqual(check_task(output)["status"], "UNCHANGED")
            self.assertIn("Source inspection only", handoff(output)["markdown"])
            source.write_text("changed\n")
            self.assertEqual(check_task(output)["_exit_code"], 1)
            with self.assertRaises(AgfError):
                handoff(output)

    def test_required_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.write_text(json.dumps({"goal": "do things", "scope": ["x"], "acceptance": []}))
            with self.assertRaises(AgfError):
                record_task(path)

    def test_malformed_repository_identity_is_actionable(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.write_text(json.dumps({"version": 1, "evidence": [], "repository": {}}))
            with self.assertRaisesRegex(AgfError, "repository identity"):
                check_task(path)

    def test_report_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.write_text(json.dumps({"goal": "do things", "scope": ["x"], "acceptance": ["done"]}))
            with self.assertRaises(AgfError):
                record_task(path, path)

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_record_inside_repository_does_not_immediately_expire(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(["git", "init", "-q", temp], check=True, capture_output=True)
            contract = root / "input.json"
            contract.write_text(json.dumps({"goal": "test", "scope": ["x"], "acceptance": ["done"]}))
            output = root / "record.json"
            record_task(contract, output, root, repo=root)
            self.assertEqual(check_task(output)["status"], "UNCHANGED")
            (root / "new.txt").write_text("new change")
            self.assertEqual(check_task(output)["status"], "STALE_OR_MISSING")
