import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

HOOK = Path(__file__).resolve().parents[1] / "templates" / "claude-continuity-hook.py"


class ContinuityHookTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "project"
        self.root.mkdir()
        self.git("init", "-q")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", "first")

    def git(self, *argv):
        subprocess.run(["git", "-C", str(self.root), *argv], check=True, capture_output=True)

    def commit(self, message):
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "--allow-empty", "-m", message)

    def hook(self, name, event, config=None):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        argv = [sys.executable, str(HOOK), name] + ([str(config)] if config else [])
        result = subprocess.run(argv, input=json.dumps(event), capture_output=True, text=True, env=env, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("failed", result.stderr)
        return result.stdout

    def test_session_start_says_nothing_without_hand_off_or_checkpoint(self):
        self.assertEqual(self.hook("session-start", {"source": "startup"}).strip(), "")

    def test_session_start_points_at_the_hand_off_and_counts_newer_commits(self):
        handoff = self.root / "HANDOFF.md"
        handoff.write_text("# hand-off\n")
        old = time.time() - 120
        os.utime(handoff, (old, old))
        self.commit("after the hand-off")
        output = json.loads(self.hook("session-start", {"source": "compact"}))
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("HANDOFF.md", context)
        self.assertIn("2 個新 commit", context, "the setup commit and this one are both newer than the back-dated hand-off")
        self.assertIn("壓縮", context)
        self.assertNotIn("systemMessage", output)

    def test_resuming_a_cold_session_tells_the_user_the_cost(self):
        (self.root / "HANDOFF.md").write_text("x")
        output = json.loads(self.hook("session-start", {"source": "resume", "prompt_cache_likely_expired": True,
                                                        "estimated_cache_write_usd": 1.234}))
        self.assertIn("1.23", output["systemMessage"])

    def test_pre_compact_prints_instructions_naming_the_hand_off(self):
        (self.root / ".ai").mkdir()
        (self.root / ".ai" / "HANDOFF.md").write_text("x")
        text = self.hook("pre-compact", {"trigger": "auto"})
        self.assertIn(".ai/HANDOFF.md", text)
        self.assertIn("下一步", text)

    def test_checkpoints_keep_the_summary_the_error_and_git_state(self):
        (self.root / "work.txt").write_text("changed")
        self.hook("post-compact", {"compact_summary": "We were fixing the pager."})
        latest = (self.root / ".agf/checkpoints/latest.md").read_text()
        self.assertIn("We were fixing the pager.", latest)
        self.assertIn("work.txt", latest)
        self.assertIn("first", latest)
        self.hook("stop-failure", {"error": "rate_limit", "last_assistant_message": "API Error: Rate limit reached"})
        latest = (self.root / ".agf/checkpoints/latest.md").read_text()
        self.assertIn("rate_limit", latest)
        self.assertIn("Rate limit reached", latest)

    def test_session_end_reads_the_last_assistant_text_from_the_transcript(self):
        transcript = self.root.parent / "t.jsonl"
        transcript.write_text("\n".join(json.dumps(line) for line in [
            {"message": {"role": "assistant", "content": [{"type": "text", "text": "old"}]}},
            {"message": {"role": "user", "content": "hi"}},
            {"message": {"role": "assistant", "content": [{"type": "text", "text": "parse() done; format() next"}]}}]))
        self.hook("session-end", {"reason": "other", "transcript_path": str(transcript)})
        latest = (self.root / ".agf/checkpoints/latest.md").read_text()
        self.assertIn("format() next", latest)
        self.assertNotIn("\nold\n", latest)

    def test_a_message_saved_at_stop_reaches_the_end_of_session_checkpoint(self):
        self.hook("stop", {"session_id": "s", "last_assistant_message": "parse() works; format() still raises"})
        self.hook("stop", {"session_id": "other", "last_assistant_message": "a different session"})
        self.hook("session-end", {"session_id": "s", "reason": "other"})
        latest = (self.root / ".agf/checkpoints/latest.md").read_text()
        self.assertIn("format() still raises", latest)
        self.assertNotIn("a different session", latest, "each session keeps its own last message")
        self.hook("stop-failure", {"session_id": "s"})
        self.assertIn("事件沒有提供", (self.root / ".agf/checkpoints/latest.md").read_text())

    def test_committing_the_hand_off_counts_as_updating_it(self):
        # Found by the S11 review: the commit that includes the hand-off is newer than the file.
        handoff = self.root / "HANDOFF.md"
        self.hook("session-start", {"source": "startup", "session_id": "s2"})
        time.sleep(1.1)
        handoff.write_text("updated")
        old = time.time() - 60
        os.utime(handoff, (old, old))
        self.git("add", "HANDOFF.md")
        self.commit("update the hand-off")
        self.assertEqual(self.hook("stop", {"session_id": "s2"}).strip(), "")
        context = json.loads(self.hook("session-start", {"source": "startup", "session_id": "s3"}))["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("新 commit", context)
        time.sleep(1.1)
        self.commit("more work")
        self.assertIn("1 個 commit", self.hook("stop", {"session_id": "s2"}))

    def test_a_resumed_old_session_keeps_its_marker(self):
        (self.root / "HANDOFF.md").write_text("x")
        folder = self.root / ".agf/checkpoints"
        self.hook("session-start", {"source": "startup", "session_id": "old"})
        self.hook("session-start", {"source": "startup", "session_id": "gone"})
        month = time.time() - 30 * 86400
        for name in (".session-old", ".session-gone"):
            os.utime(folder / name, (month, month))
        self.hook("session-start", {"source": "resume", "session_id": "old"})
        self.assertTrue((folder / ".session-old").is_file())
        self.assertFalse((folder / ".session-gone").exists())

    def test_only_the_newest_checkpoints_are_kept(self):
        config = self.root.parent / "c.json"
        config.write_text(json.dumps({"keep": 2}))
        for index in range(4):
            self.hook("post-compact", {"compact_summary": f"summary {index}"}, config)
            time.sleep(1.05)
        copies = [p for p in (self.root / ".agf/checkpoints").glob("*-*.md")]
        self.assertEqual(len(copies), 2)

    def test_model_switch_warns_only_when_the_warm_cache_is_expensive(self):
        cheap = self.hook("pre-model-switch", {"from_model": "a", "to_model": "b", "prompt_cache_warm": True, "estimated_cache_write_usd": 0.1})
        self.assertEqual(cheap.strip(), "")
        costly = json.loads(self.hook("pre-model-switch", {"from_model": "a", "to_model": "b", "prompt_cache_warm": True,
                                                           "estimated_cache_write_usd": 0.8, "context_tokens": 200000}))
        self.assertIn("0.80", costly["systemMessage"])
        self.assertNotIn("decision", costly)
        config = self.root.parent / "block.json"
        config.write_text(json.dumps({"block_switch": True}))
        blocked = json.loads(self.hook("pre-model-switch", {"to_model": "b", "prompt_cache_warm": True, "estimated_cache_write_usd": 0.8}, config))
        self.assertEqual(blocked["decision"], "block")

    def test_stop_reminds_once_about_commits_made_in_this_session(self):
        handoff = self.root / "HANDOFF.md"
        handoff.write_text("x")
        old = time.time() - 120
        os.utime(handoff, (old, old))
        # The setup commit is newer than the hand-off but older than the session: no reminder for it.
        self.assertEqual(self.hook("stop", {"session_id": "s1"}).strip(), "", "a session without a start record is not judged")
        time.sleep(1.1)
        self.hook("session-start", {"source": "startup", "session_id": "s1"})
        self.assertEqual(self.hook("stop", {"session_id": "s1"}).strip(), "", "nothing was committed in this session yet")
        time.sleep(1.1)
        self.commit("new work")
        reminder = json.loads(self.hook("stop", {"session_id": "s1"}))
        self.assertIn("1 個 commit", reminder["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.hook("stop", {"session_id": "s1"}).strip(), "", "only once per session")
        self.assertEqual(self.hook("stop", {"session_id": "s1", "stop_hook_active": True}).strip(), "")

    def test_prompts_are_kept_only_when_asked_and_reach_the_checkpoint(self):
        # A decision made only in chat ("the README is out of date") must survive a cut-off session.
        event = {"session_id": "p1", "prompt": "Implement it; the README's format is out of date, use 1h02m03s."}
        self.assertEqual(self.hook("user-prompt", event).strip(), "", "UserPromptSubmit output would join the prompt")
        self.hook("session-end", {"session_id": "p1", "reason": "other"})
        self.assertNotIn("1h02m03s", (self.root / ".agf/checkpoints/latest.md").read_text(), "off by default")
        config = self.root.parent / "prompts.json"
        config.write_text(json.dumps({"save_prompts": True}))
        for index in range(7):
            self.hook("user-prompt", {"session_id": "p2", "prompt": f"message {index}"}, config)
        self.hook("user-prompt", {"session_id": "p2", "prompt": event["prompt"]}, config)
        self.hook("user-prompt", {"session_id": "other", "prompt": "from another session"}, config)
        self.hook("session-end", {"session_id": "p2", "reason": "other"}, config)
        latest = (self.root / ".agf/checkpoints/latest.md").read_text()
        self.assertIn("1h02m03s", latest)
        self.assertIn("message 6", latest)
        self.assertNotIn("message 2", latest, "only the newest five are shown")
        self.assertNotIn("from another session", latest)

    def test_broken_input_or_configuration_never_stops_the_session(self):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.root))
        for argv, stdin in [([sys.executable, str(HOOK), "stop"], "not json"),
                            ([sys.executable, str(HOOK), "session-start", "/missing.json"], "{}"),
                            ([sys.executable, str(HOOK), "nonsense"], "{}")]:
            result = subprocess.run(argv, input=stdin, capture_output=True, text=True, env=env, timeout=20)
            self.assertEqual(result.returncode, 0, argv)
        for content in ["[1, [2]]", '{"keep": 0}', '{"keep": "3"}', '{"handoff_files": "HANDOFF.md"}']:
            config = self.root.parent / "odd.json"
            config.write_text(content)
            result = subprocess.run([sys.executable, str(HOOK), "session-end", str(config)], input="{}", capture_output=True,
                                    text=True, env=env, timeout=20)
            self.assertEqual(result.returncode, 0, content)
            self.assertIn("agf continuity", result.stderr, content)

    def test_outside_a_git_repository_checkpoints_still_work(self):
        plain = self.root.parent / "plain"
        plain.mkdir()
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(plain))
        subprocess.run([sys.executable, str(HOOK), "session-end"], input="{}", text=True, env=env, timeout=20, check=True)
        self.assertTrue((plain / ".agf/checkpoints/latest.md").is_file())


if __name__ == "__main__":
    unittest.main()
