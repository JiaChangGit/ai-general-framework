"""What Git would publish from this repository (S18).

S17 committed raw host event streams by staging a whole measurement folder. They hold
session ids, local paths, the installed plugins and skills, and quota state.
"""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
STREAM_DIR = re.compile(r"(?:^|/)streams/")
HOST_OUTPUT = (".stderr", ".meta.json")  # what run_claude.py writes next to a stream
EVENT_STREAM = re.compile(r'"session_id"\s*:\s*"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-')


def offending(paths, read):
    found = []
    for path in paths:
        if (STREAM_DIR.search(path) or path.endswith(HOST_OUTPUT)
                or (path.endswith((".jsonl", ".json", ".log", ".txt")) and EVENT_STREAM.search(read(path)))):
            found.append(path)
    return found


@unittest.skipUnless(shutil.which("git") and (ROOT / ".git").exists(), "not a Git checkout")
class PublishedFilesTests(unittest.TestCase):
    def test_no_raw_event_stream_is_tracked(self):
        listed = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, check=True).stdout
        paths = [path for path in listed.decode("utf-8").split("\0") if path]

        def read(path):
            file = ROOT / path
            return file.read_text(encoding="utf-8", errors="replace") if file.is_file() else ""

        self.assertEqual(offending(paths, read), [],
                         "Raw host event streams must stay local. Keep the file and untrack it: git rm -r --cached -- <path>; "
                         "commit only results.json, reports and the extracted texts.")


class RuleTests(unittest.TestCase):
    def test_streams_are_recognised_by_folder_and_by_content(self):
        event = '{"type":"system","session_id":"0f3c9e2a-1111-2222-3333-444455556666"}'
        texts = {"studies/a/streams/x.stderr": "", "studies/a/renamed.jsonl": event, "studies/a/results.json": '{"runs": []}'}
        self.assertEqual(offending(list(texts), texts.__getitem__), ["studies/a/streams/x.stderr", "studies/a/renamed.jsonl"])
        outside = {"studies/a/x.stderr": "", "evals/out/x.meta.json": "{}", "evals/saved.jsonl": event, "docs/guide.md": event}
        self.assertEqual(offending(list(outside), outside.__getitem__), list(outside)[:3])


if __name__ == "__main__":
    unittest.main()
