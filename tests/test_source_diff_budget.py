import argparse
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agf.common import AgfError
from agf.sources import _diff


class SourceDiffBudgetTests(unittest.TestCase):
    def test_repeated_inputs_stop_before_quadratic_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            left, right = Path(temp) / 'left.txt', Path(temp) / 'right.txt'
            left.write_text('a\n' * 8000, encoding='utf-8')
            right.write_text('a\n' * 7999 + 'b\n', encoding='utf-8')
            args = argparse.Namespace(before=left, after=right, limit=1, max_chars=10)
            with patch('agf.sources.difflib.SequenceMatcher') as matcher:
                with self.assertRaisesRegex(AgfError, 'unit/work budget'):
                    _diff(args)
                matcher.assert_not_called()
            right.write_bytes(left.read_bytes())
            with patch('agf.sources.difflib.SequenceMatcher') as matcher:
                result = _diff(args)
                matcher.assert_not_called()
            self.assertEqual(result['total_change_groups'], 0)
            self.assertFalse(result['truncated'])
