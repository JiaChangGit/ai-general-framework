"""HANDOFF.md holds commands that check the state, never one-time commands that change it (S22).

Merge and deletion commands went stale there three times, and the last copy could have been pasted
again. Such commands are given to the user in the reply of the round that needs them.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHANGES = re.compile(r"\brm\b|\bpush\b|\bpull\b|--apply\b|\bprune\b|\bgc\b|\breflog expire\b|\bimage rm\b")


class HandoffTests(unittest.TestCase):
    def test_command_blocks_only_check_the_state(self):
        text = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
        blocks = re.findall(r"```bash\n(.*?)```", text, re.S)
        self.assertTrue(blocks, "the hand-off must keep commands that check the state")
        changing = [line for block in blocks for line in block.splitlines() if CHANGES.search(line)]
        self.assertEqual(changing, [])


if __name__ == "__main__":
    unittest.main()
