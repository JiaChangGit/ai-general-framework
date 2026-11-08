import argparse
import hashlib
import json
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
                      "nodes": [{"id": "Caller", "label": '呼叫 "<tag>"'}, {"id": "Worker", "label": "工作"}],
                      "edges": [{"from": "Caller", "to": "Worker", "label": "call"}]}

    def test_mermaid_modes_preserve_sources(self):
        for kind, declaration in (("flowchart", "flowchart LR"), ("sequence", "sequenceDiagram"), ("state", "stateDiagram-v2")):
            result = diagrams.mermaid({**self.model, "kind": kind})
            self.assertTrue(result.startswith("---\nconfig:\n  look: neo\n"))
            self.assertIn(declaration, result)
            self.assertIn("src/example.c", result)
            self.assertIn("#quot;#lt;tag#gt;#quot;" if kind == "sequence" else "&quot;&lt;tag&gt;&quot;", result)
            self.assertNotIn('呼叫 "<tag>"', result)

    def test_sequence_semicolon_and_entity_input_are_not_statements(self):
        result = diagrams.mermaid({"kind": "sequence", "nodes": [{"id": "A", "label": '"A"<3;#59;'}], "edges": []})
        self.assertIn("#59;", result)
        self.assertNotIn("&#59;", result)
        self.assertIn("#35;59#59;", result)
        self.assertEqual(sum(line.lstrip().startswith("participant ") for line in result.splitlines()), 1)

    def test_node_limits_reject_without_truncating(self):
        for nodes in ([], [{"id": f"N{i}", "label": "節點"} for i in range(16)],
                      [{"id": "A", "label": "中文字" * 5}], [{"id": "A", "label": "<br/>"}]):
            with self.subTest(nodes=len(nodes)), self.assertRaises(AgfError):
                diagrams.mermaid({"nodes": nodes})
        self.assertEqual(diagrams.mermaid({"nodes": [{"id": "A", "label": "字" * 12}]}).count("字"), 12)

    def test_line_breaks_preserve_escaped_text_in_all_formats(self):
        model = {"nodes": [{"id": "A", "label": "輸入<br/>檢查 <x>"}], "edges": []}
        for kind in ("flowchart", "sequence", "state"):
            with self.subTest(kind=kind):
                value = diagrams.mermaid({**model, "kind": kind})
                self.assertIn("輸入<br/>檢查", value)
                self.assertNotIn("檢查 <x>", value)
        root = ET.fromstring(diagrams.drawio(model))
        self.assertEqual(root.find('.//mxCell[@id="A"]').get("value"), "輸入\n檢查 <x>")

    def test_decision_branches_require_labels_and_preserve_only_supplied_edges(self):
        model = {"nodes": [{"id": "Check", "label": "資料有效？", "shape": "decision"},
                           {"id": "Continue", "label": "繼續"}, {"id": "Return", "label": "退回"}],
                 "edges": [{"from": "Check", "to": "Continue", "label": "是"},
                           {"from": "Check", "to": "Return", "label": "否"}]}
        value = diagrams.mermaid(model)
        self.assertIn('Check{"資料有效？"}', value)
        self.assertEqual(value.count(" -->"), 2)
        self.assertIn('Check -->|"是"| Continue', value)
        root = ET.fromstring(diagrams.drawio(model))
        self.assertIn("rhombus;", root.find('.//mxCell[@id="Check"]').get("style"))
        model["edges"][1].pop("label")
        for renderer in (diagrams.mermaid, diagrams.drawio):
            with self.assertRaisesRegex(AgfError, "decision branch"):
                renderer(model)
        model["edges"][1]["label"] = "<br/>"
        with self.assertRaisesRegex(AgfError, "decision branch"):
            diagrams.mermaid(model)

    def test_header_check_accepts_templates_without_claiming_syntax_validation(self):
        source = self.root / "圖.mmd"
        for declaration in ("flowchart LR", "sequenceDiagram", "stateDiagram-v2", "block-beta", "block", "timeline", "gantt"):
            source.write_text(diagrams.MERMAID_HEADER + "\n%% example\n" + declaration + "\n", encoding="utf-8")
            result = invoke("diagram", "validate", str(source), "--format", "mermaid")
            self.assertEqual(result["status"], "HEADER_RECOGNIZED")
            self.assertEqual(result["style_warnings"], [])
            self.assertIn("not a Mermaid parser", result["limitation"])
        source.write_text("flowchart LR\n intentionally invalid body\n", encoding="utf-8")
        self.assertTrue(invoke("diagram", "validate", str(source), "--format", "mermaid")["style_warnings"])
        source.write_text("---\nconfig:\n  theme: neutral\n  look: neo\n---\nflowchart LR\n", encoding="utf-8")
        self.assertTrue(invoke("diagram", "validate", str(source), "--format", "mermaid")["style_warnings"])
        source.write_text("---\nconfig:\n  look: neo\nflowchart LR\n", encoding="utf-8")
        with self.assertRaisesRegex(AgfError, "Unclosed"):
            invoke("diagram", "validate", str(source), "--format", "mermaid")

    def test_unknown_edges_and_duplicate_ids_rejected(self):
        with self.assertRaises(AgfError):
            diagrams.mermaid({**self.model, "edges": [{"from": "Caller", "to": "Missing"}]})
        with self.assertRaises(AgfError):
            diagrams.drawio({**self.model, "nodes": [self.model["nodes"][0]] * 2})
        for shape in ([], {}, True):
            with self.subTest(shape=shape), self.assertRaises(AgfError):
                diagrams.mermaid({"nodes": [{"id": "A", "label": "節點", "shape": shape}]})
        with self.assertRaises(AgfError):
            diagrams.mermaid({**self.model, "kind": []})

    def test_drawio_roundtrip_and_edge_id_collision(self):
        self.model["nodes"].append({"id": "agf_edge_0", "label": "像邊線的節點"})
        value = diagrams.drawio(self.model)
        self.assertEqual(diagrams.validate_drawio(value)["status"], "STRUCTURE_VALID")
        root = ET.fromstring(value)
        self.assertIn("src/example.c", root.attrib["agf_sources"])
        self.assertEqual(root.find('.//mxCell[@id="Caller"]').get("value"), '呼叫 "<tag>"')

    def test_drawio_rejects_entity_and_invalid_reference(self):
        with self.assertRaises(AgfError):
            diagrams.validate_drawio('<!DOCTYPE a [<!ENTITY x "boom">]><mxfile/>')
        value = diagrams.drawio(self.model).replace('target="Worker"', 'target="Missing"')
        with self.assertRaises(AgfError):
            diagrams.validate_drawio(value)

    def test_transitions_group_interleaved_events_in_file_order_and_count_repeats(self):
        source = self.root / "events.csv"
        # Deliberately unsorted timestamps: timestamps must not redefine adjacency.
        source.write_text("time,device,state\n30,A,Idle\n20,B,Busy\n10,A,Busy\n"
                          "40,A,Busy\n5,B,Done\n50,A,Idle\n", encoding="utf-8")
        result = invoke("diagram", "transitions", str(source), "--state-column", "state", "--group-column", "device")
        ids = {node["label"]: node["id"] for node in result["nodes"]}
        counts = {(edge["from"], edge["to"]): int(edge["label"]) for edge in result["edges"]}
        self.assertEqual(counts, {(ids["Idle"], ids["Busy"]): 1, (ids["Busy"], ids["Busy"]): 1,
                                  (ids["Busy"], ids["Done"]): 1, (ids["Busy"], ids["Idle"]): 1})
        self.assertEqual(result["statistics"]["events"], 6)
        self.assertEqual(result["statistics"]["groups"], 2)
        self.assertEqual(result["statistics"]["transitions"], 4)
        self.assertEqual(result["statistics"]["self_transitions"], 1)
        self.assertIn("no timestamp sorting", result["statistics"]["ordering"])
        self.assertEqual(result["sources"][0]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertIn("stateDiagram-v2", diagrams.mermaid(result))

    def test_transitions_accept_bom_quoted_delimiters_and_non_csv_extensions(self):
        for delimiter, separator, suffix in (("comma", ",", ".csv"), ("tab", "\t", ".txt"), ("pipe", "|", ".log")):
            with self.subTest(delimiter=delimiter):
                source = self.root / ("events" + suffix)
                source.write_text(f'state{separator}note\n"A,B"{separator}"x{separator}y"\nDone{separator}z\n', encoding="utf-8-sig")
                result = invoke("diagram", "transitions", str(source), "--state-column", "state", "--delimiter", delimiter)
                self.assertEqual(result["statistics"]["transitions"], 1)
                self.assertEqual(result["nodes"][0]["label"], "A,B")

    def test_transition_json_can_feed_create_with_safe_identifiers_and_literal_labels(self):
        source, model, output = self.root / "events.csv", self.root / "stats.json", self.root / "states.mmd"
        source.write_text('state\n"A->B"\n"<tag>"\n"A->B"\n', encoding="utf-8")
        created = invoke("diagram", "transitions", str(source), "--state-column", "state", "--output", str(model))
        self.assertEqual(created["status"], "CREATED")
        data = json.loads(model.read_text(encoding="utf-8"))
        self.assertEqual([node["id"] for node in data["nodes"]], ["S0", "S1"])
        invoke("diagram", "create", str(model), "--format", "mermaid", "--output", str(output))
        text = output.read_text(encoding="utf-8")
        self.assertIn('state "A-&gt;B" as S0', text)
        self.assertIn('state "&lt;tag&gt;" as S1', text)
        before = model.read_bytes()
        with self.assertRaises(AgfError):
            invoke("diagram", "transitions", str(source), "--state-column", "state", "--output", str(model))
        self.assertEqual(model.read_bytes(), before)

    def test_transitions_fail_closed_on_missing_or_ambiguous_data_without_output(self):
        source, output = self.root / "events.log", self.root / "stats.json"
        cases = ["", "state,state\nIdle,Idle\n", "other\nIdle\n", "state\n", "state,note\nIdle\n",
                 "state\nIdle,extra\n", 'state\n"unfinished\n', 'state\n""\n', "state\n Idle\n",
                 "state\n" + "字" * 13 + "\n", 'state\n"A\nB"\n', "state\n<br/>\n", "state\nA<br>B\n"]
        for content in cases:
            with self.subTest(content=repr(content)):
                source.write_text(content, encoding="utf-8")
                with self.assertRaises(AgfError):
                    invoke("diagram", "transitions", str(source), "--state-column", "state", "--output", str(output))
                self.assertFalse(output.exists())
        source.write_bytes(b"state\n\xff\n")
        with self.assertRaisesRegex(AgfError, "UTF-8"):
            invoke("diagram", "transitions", str(source), "--state-column", "state", "--output", str(output))
        source.write_text("state,device\nIdle,\n", encoding="utf-8")
        with self.assertRaisesRegex(AgfError, "Empty group"):
            invoke("diagram", "transitions", str(source), "--state-column", "state", "--group-column", "device", "--output", str(output))
        self.assertFalse(output.exists())

    def test_transitions_reject_state_and_row_overflow_without_partial_output(self):
        source, output = self.root / "events.csv", self.root / "stats.json"
        source.write_text("state\n" + "\n".join(f"state{i}" for i in range(16)) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(AgfError, "15 observed states"):
            invoke("diagram", "transitions", str(source), "--state-column", "state", "--output", str(output))
        self.assertFalse(output.exists())
        source.write_text("state\n" + "Idle\n" * 100_001, encoding="utf-8")
        with self.assertRaisesRegex(AgfError, "100000 rows"):
            invoke("diagram", "transitions", str(source), "--state-column", "state", "--output", str(output))
        self.assertFalse(output.exists())

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
