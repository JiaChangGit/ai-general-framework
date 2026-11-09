import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess

from agf.common import AgfError
from agf.evidence import check_task, handoff, record_task


class EvidenceTests(unittest.TestCase):
    def test_handoff_preserves_resume_context_and_observation_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            contract = root / "input.json"
            details = {
                "goal": "Fix retry handling", "scope": ["queue.py"], "acceptance": ["Failed batches leave state unchanged"],
                "verification": ["2026-11-09: queue regression passes; integration suite not run"],
                "next_steps": ["Read the current diff, then run the integration scenario"],
                "boundaries": ["Local edits only; deployment requires separate authorization"],
            }
            contract.write_text(json.dumps(details))
            output = root / "record.json"
            result = record_task(contract, output, root)
            self.assertEqual(datetime.fromisoformat(result["recorded_at"]).utcoffset(), timedelta(0))
            report = handoff(output)["markdown"]
            for field in ("verification", "next_steps", "boundaries"):
                self.assertEqual(result[field], details[field])
                self.assertIn(details[field][0], report)
            self.assertIn(result["recorded_at"], report)

    def test_invalid_resume_fields_are_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            contract = root / "input.json"
            output = root / "record.json"
            for field in ("verification", "next_steps", "boundaries"):
                for value in ("looks valid", [42], [" "]):
                    with self.subTest(field=field, value=value):
                        contract.write_text(json.dumps({"goal": "test", "scope": ["x"], "acceptance": ["done"], field: value}))
                        with self.assertRaisesRegex(AgfError, field):
                            record_task(contract, output, root)
                        self.assertFalse(output.exists())

    def test_legacy_record_without_resume_fields_still_generates_handoff(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "record.json"
            path.write_text(json.dumps({"version": 1, "goal": "test", "scope": ["x"], "acceptance": ["done"], "evidence": []}))
            self.assertEqual(check_task(path)["status"], "UNCHANGED")
            self.assertIn("## Next steps\n\n- None recorded.", handoff(path)["markdown"])

    def test_handoff_rejects_malformed_contract_instead_of_splitting_characters(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "record.json"
            for field in ("scope", "verification", "next_steps", "boundaries"):
                with self.subTest(field=field):
                    data = {"version": 1, "goal": "test", "scope": ["queue.py"], "acceptance": ["done"], "evidence": [], field: "incorrect type"}
                    path.write_text(json.dumps(data))
                    with self.assertRaisesRegex(AgfError, field):
                        handoff(path)

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
            for repository in ({}, {"repo": temp, "tracked_diff_sha256": "x", "status_sha256": "y"},
                               {"repo": temp, "head": 42, "tracked_diff_sha256": "x", "status_sha256": "y"}):
                with self.subTest(repository=repository):
                    path.write_text(json.dumps({"version": 1, "evidence": [], "repository": repository}))
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
