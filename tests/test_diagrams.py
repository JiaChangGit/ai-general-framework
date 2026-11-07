import argparse
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from agf import diagrams
from agf.common import AgfError


def invoke(*argv):
    parser = argparse.ArgumentParser()
    diagrams.register(parser.add_subparsers(required=True))
    args = parser.parse_args(argv)
    return args.func(args)


class DiagramTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agf-diagrams-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = {"sources": [{"path": "src/example.c", "line": 12}],
                      "nodes": [{"id": "Caller", "label": 'caller "<tag>"'}, {"id": "Worker", "label": "工作"}],
                      "edges": [{"from": "Caller", "to": "Worker", "label": "call"}]}

    def test_mermaid_modes_preserve_sources(self):
        for kind, declaration in (("flowchart", "flowchart LR"), ("sequence", "sequenceDiagram"), ("state", "stateDiagram-v2")):
            result = diagrams.mermaid({**self.model, "kind": kind})
            self.assertIn(declaration, result)
            self.assertIn("src/example.c", result)
            self.assertIn("#quot;#lt;tag#gt;#quot;" if kind == "sequence" else "&quot;&lt;tag&gt;&quot;", result)
            self.assertNotIn('caller "<tag>"', result)

    def test_sequence_semicolon_and_entity_input_are_not_statements(self):
        result = diagrams.mermaid({"kind": "sequence", "nodes": [{"id": "A", "label": '輸入 "A" < 3; 檢查 #59;'}], "edges": []})
        self.assertIn("#59;", result)
        self.assertNotIn("&#59;", result)
        self.assertIn("#35;59#59;", result)
        self.assertEqual(len(result.splitlines()), 3)

    def test_unknown_edges_and_duplicate_ids_rejected(self):
        with self.assertRaises(AgfError):
            diagrams.mermaid({**self.model, "edges": [{"from": "Caller", "to": "Missing"}]})
        with self.assertRaises(AgfError):
            diagrams.drawio({**self.model, "nodes": [self.model["nodes"][0]] * 2})

    def test_drawio_roundtrip_and_edge_id_collision(self):
        self.model["nodes"].append({"id": "agf_edge_0", "label": "edge-looking node"})
        value = diagrams.drawio(self.model)
        self.assertEqual(diagrams.validate_drawio(value)["status"], "STRUCTURE_VALID")
        root = ET.fromstring(value)
        self.assertIn("src/example.c", root.attrib["agf_sources"])
        self.assertEqual(root.find('.//mxCell[@id="Caller"]').get("value"), 'caller "<tag>"')

    def test_drawio_rejects_entity_and_invalid_reference(self):
        with self.assertRaises(AgfError):
            diagrams.validate_drawio('<!DOCTYPE a [<!ENTITY x "boom">]><mxfile/>')
        value = diagrams.drawio(self.model).replace('target="Worker"', 'target="Missing"')
        with self.assertRaises(AgfError):
            diagrams.validate_drawio(value)

    def test_gdb_html_escapes_trace_and_source(self):
        rows, ignored = diagrams.parse_trace('thread header\n#0 <script>alert(1)</script>\n#1 work()\n', "gdb")
        value = diagrams.trace_html(rows, "gdb", '<img src=x onerror="boom">', "0" * 64, ignored)
        self.assertEqual(rows[0]["line"], 2)
        self.assertEqual(ignored, 1)
        self.assertNotIn("<script>alert(1)</script>", value)
        self.assertIn("&lt;script&gt;", value)
        self.assertIn("&lt;img", value)

    def test_ftrace_records_and_unknown_lines(self):
        rows, ignored = diagrams.parse_trace("# header\n 0) | schedule() {\nworker-1 [000] .... 12.345: sched_switch: prev=1 next=2\nunknown\n", "ftrace")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["line"], 3)
        self.assertEqual(ignored, 2)

    def test_empty_trace_does_not_create_output(self):
        source, output = self.root / "trace.txt", self.root / "trace.html"
        source.write_text("not a recognized trace")
        with self.assertRaises(AgfError):
            invoke("diagram", "trace", str(source), "--format", "gdb", "--output", str(output))
        self.assertFalse(output.exists())

    def test_render_requires_explicit_execution(self):
        source, output = self.root / "input.mmd", self.root / "output.svg"
        source.write_text("flowchart LR\n A --> B\n")
        with patch.object(diagrams, "run_command") as run:
            result = invoke("diagram", "render", str(source), "--format", "mermaid", "--output", str(output))
        self.assertEqual(result["status"], "PLAN")
        run.assert_not_called()
        self.assertFalse(output.exists())

    def test_render_absent_tool_is_unavailable(self):
        source = self.root / "input.mmd"
        source.write_text("flowchart LR")
        with patch.object(diagrams.shutil, "which", return_value=None):
            result = invoke("diagram", "render", str(source), "--format", "mermaid", "--output", str(self.root / "out.svg"), "--execute")
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_native_renderer_argv_output_and_exit_status(self):
        source, output = self.root / "中文 $input.mmd", self.root / "output.svg"
        source.write_text("flowchart LR")
        renderer = self.root / "fake renderer.py"
        renderer.write_text('import argparse\nfrom pathlib import Path\np=argparse.ArgumentParser();p.add_argument("-i");p.add_argument("-o");a=p.parse_args()\nassert Path(a.i).read_text()=="flowchart LR"\nPath(a.o).write_text("<svg/>")\n')
        result = invoke("diagram", "render", str(source), "--format", "mermaid", "--output", str(output),
                        "--tool", sys.executable, "--tool-arg", str(renderer), "--execute")
        self.assertEqual(result["status"], "RENDERED")
        self.assertEqual(result["execution"]["argv"][1], str(renderer))
        self.assertEqual(output.read_text(), "<svg/>")
        with self.assertRaises(AgfError):
            invoke("diagram", "render", str(source), "--format", "mermaid", "--output", str(output), "--execute")

    def test_renderer_failure_never_publishes_output(self):
        source, output = self.root / "input.mmd", self.root / "output.svg"
        source.write_text("flowchart LR")
        renderer = self.root / "failing.py"
        renderer.write_text("raise SystemExit(7)\n")
        with self.assertRaisesRegex(AgfError, "exit 7"):
            invoke("diagram", "render", str(source), "--format", "mermaid", "--output", str(output),
                   "--tool", sys.executable, "--tool-arg", str(renderer), "--execute")
        self.assertFalse(output.exists())

    def test_renderer_timeout_does_not_publish_output(self):
        source, output = self.root / "input.mmd", self.root / "out.svg"
        source.write_text("flowchart LR")
        renderer = self.root / "sleep.py"
        renderer.write_text("import time\ntime.sleep(30)\n")
        with self.assertRaisesRegex(AgfError, "timeout=True"):
            invoke("diagram", "render", str(source), "--format", "mermaid", "--output", str(output),
                   "--tool", sys.executable, "--tool-arg", str(renderer), "--timeout", "1", "--execute")
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
