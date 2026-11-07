"""Evidence-preserving diagrams, optional native rendering and trace browsing."""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET

from .common import AgfError, read_json, write_text
from .execution import run_command


def _model(data: dict) -> tuple[list, list, list]:
    if not isinstance(data, dict):
        raise AgfError("Diagram input must be a JSON object")
    nodes, edges, sources = data.get("nodes", []), data.get("edges", []), data.get("sources", [])
    if not isinstance(nodes, list) or not isinstance(edges, list) or not isinstance(sources, list):
        raise AgfError("nodes, edges and sources must be arrays")
    ids = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", node["id"]):
            raise AgfError("Each node needs a portable identifier")
        if node["id"] in ids or node["id"] in {"end", "participant", "state", "note"}:
            raise AgfError("Duplicate or reserved node identifier")
        if not isinstance(node.get("label"), str):
            raise AgfError("Each node needs a string label")
        ids.add(node["id"])
    for edge in edges:
        if (not isinstance(edge, dict) or not isinstance(edge.get("from"), str) or not isinstance(edge.get("to"), str)
                or edge["from"] not in ids or edge["to"] not in ids):
            raise AgfError("Edge references an unknown node")
        if not isinstance(edge.get("label", ""), str):
            raise AgfError("Edge label must be a string")
    return nodes, edges, sources


def _label(value: str) -> str:
    entities = {"&": "&amp;", '"': "&quot;", "<": "&lt;", ">": "&gt;", ";": "&#59;"}
    return "".join(entities.get(char, char) for char in value.replace("\r", " ").replace("\n", " "))


def _sequence_label(value: str) -> str:
    # Sequence syntax uses Mermaid entity codes, not HTML ampersand entities:
    # semicolons otherwise become statement separators before label rendering.
    entities = {"#": "#35;", "&": "#38;", '"': "#quot;", "<": "#lt;", ">": "#gt;", ";": "#59;", "|": "#124;"}
    return "".join(entities.get(char, char) for char in value.replace("\r", " ").replace("\n", " "))


def mermaid(data: dict) -> str:
    nodes, edges, sources = _model(data)
    kind = data.get("kind", "flowchart")
    if kind not in {"flowchart", "sequence", "state"}:
        raise AgfError("Supported diagram kinds: flowchart, sequence, state")
    lines = ["%% Sources: " + json.dumps(sources, ensure_ascii=True)]
    if kind == "sequence":
        lines.append("sequenceDiagram")
        lines.extend(f'    participant {n["id"]} as {_sequence_label(n["label"])}' for n in nodes)
        lines.extend(f'    {e["from"]}->>{e["to"]}: {_sequence_label(e.get("label", ""))}' for e in edges)
    elif kind == "state":
        lines.append("stateDiagram-v2")
        lines.extend(f'    state "{_label(n["label"])}" as {n["id"]}' for n in nodes)
        lines.extend(f'    {e["from"]} --> {e["to"]}' + (": " + _label(e["label"]) if e.get("label") else "") for e in edges)
    else:
        lines.append("flowchart LR")
        lines.extend(f'    {n["id"]}["{_label(n["label"])}"]' for n in nodes)
        for edge in edges:
            suffix = '|"' + _label(edge["label"]).replace("|", "&#124;") + '"|' if edge.get("label") else ""
            lines.append(f'    {edge["from"]} -->{suffix} {edge["to"]}')
    return "\n".join(lines) + "\n"


def drawio(data: dict) -> str:
    nodes, edges, sources = _model(data)
    document = ET.Element("mxfile", {"host": "app.diagrams.net", "agf_sources": json.dumps(sources, ensure_ascii=False)})
    diagram = ET.SubElement(document, "diagram", {"id": "agf", "name": "Evidence diagram"})
    graph = ET.SubElement(diagram, "mxGraphModel")
    root = ET.SubElement(graph, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    for index, node in enumerate(nodes):
        attributes = {"id": node["id"], "value": node["label"], "vertex": "1", "parent": "1",
                      "style": "rounded=1;whiteSpace=wrap;html=0;"}
        if "source" in node:
            attributes["agf_source"] = json.dumps(node["source"], ensure_ascii=False)
        cell = ET.SubElement(root, "mxCell", attributes)
        ET.SubElement(cell, "mxGeometry", {"x": str(40 + (index % 4) * 220), "y": str(40 + (index // 4) * 130),
                                            "width": "180", "height": "70", "as": "geometry"})
    for index, edge in enumerate(edges):
        edge_id = f"agf_edge_{index}"
        while any(node["id"] == edge_id for node in nodes):
            edge_id += "_"
        cell = ET.SubElement(root, "mxCell", {"id": edge_id, "edge": "1", "parent": "1",
                                               "source": edge["from"], "target": edge["to"], "value": edge.get("label", ""),
                                               "style": "edgeStyle=orthogonalEdgeStyle;html=0;endArrow=block;"})
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    return ET.tostring(document, encoding="unicode", xml_declaration=True) + "\n"


def validate_drawio(text: str) -> dict:
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise AgfError("DTD/entity declarations are not accepted")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise AgfError(f"Invalid draw.io XML: {exc}") from exc
    models = [root] if root.tag == "mxGraphModel" else root.findall("./diagram/mxGraphModel")
    if not models:
        raise AgfError("Only uncompressed draw.io mxGraphModel XML is supported")
    count = 0
    for model in models:
        cells = model.findall("./root/mxCell")
        ids = [cell.get("id") for cell in cells]
        if None in ids or len(ids) != len(set(ids)):
            raise AgfError("Duplicate or missing draw.io cell IDs")
        for cell in cells:
            if cell.get("edge") == "1" and (not cell.get("source") or not cell.get("target")):
                raise AgfError("draw.io edges require source and target references")
            for key in ("parent", "source", "target"):
                if cell.get(key) is not None and cell.get(key) not in ids:
                    raise AgfError(f"Unknown draw.io {key} reference")
        count += len(cells)
    return {"status": "STRUCTURE_VALID", "models": len(models), "cells": count,
            "limitation": "XML/reference checks only; native rendering verifies presentation separately."}


def _create(args):
    source = Path(args.input)
    data = read_json(source)
    result = mermaid(data) if args.format == "mermaid" else drawio(data)
    if args.format == "drawio":
        validate_drawio(result)
    output = str(write_text(args.output, result)) if args.output else None
    return {"status": "CREATED" if output else "PREVIEW", "format": args.format, "output": output,
            "content": None if output else result, "sources": data.get("sources", []),
            "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "limitation": "Relations come from the input model; source truth and layout are not automatically verified."}


def _validate(args):
    text = Path(args.input).read_text(encoding="utf-8-sig")
    if args.format == "drawio":
        return validate_drawio(text)
    content = re.sub(r"^```mermaid\s*\n|\n```\s*$", "", text.strip())
    meaningful = [line.strip() for line in content.splitlines() if line.strip() and not line.lstrip().startswith("%%")]
    if not meaningful or not re.match(r"^(flowchart\s|graph\s|sequenceDiagram$|stateDiagram(?:-v2)?$)", meaningful[0]):
        raise AgfError("Unsupported or missing Mermaid diagram declaration")
    return {"status": "HEADER_RECOGNIZED", "limitation": "Not a Mermaid parser. Use explicit native render for syntax/layout verification."}


def _render(args):
    source, output = Path(args.input).resolve(), Path(args.output).absolute()
    if not source.is_file():
        raise AgfError(f"Input not found: {source}")
    if output.exists() or output.is_symlink():
        raise AgfError(f"Output already exists: {output}")
    extension = output.suffix.lower().lstrip(".")
    if extension not in {"svg", "png", "pdf"}:
        raise AgfError("Render output must be SVG, PNG or PDF")
    if not 1 <= args.timeout <= 300:
        raise AgfError("timeout must be between 1 and 300 seconds")
    tool_name = args.tool or ("mmdc" if args.format == "mermaid" else "drawio")
    if not args.execute:
        return {"status": "PLAN", "tool": tool_name, "tool_args": args.tool_arg,
                "input": str(source), "output": str(output), "executed": False}
    executable = shutil.which(tool_name)
    if not executable:
        return {"status": "UNAVAILABLE", "tool": tool_name, "executed": False, "_exit_code": 3}
    if Path(executable).suffix.lower() in {".cmd", ".bat"}:
        raise AgfError("Batch launchers need a host-specific adapter; pass a native executable, not a .cmd/.bat shim")
    with tempfile.TemporaryDirectory(prefix="agf-render-") as directory:
        temporary = Path(directory) / ("render." + extension)
        prefix = [executable, *args.tool_arg]
        argv = (prefix + ["-i", str(source), "-o", str(temporary)] if args.format == "mermaid" else
                prefix + ["--export", "--format", extension, "--output", str(temporary), str(source)])
        result = run_command(argv, cwd=source.parent, timeout=args.timeout, max_chars=1500)
        if result["exit_code"] or not temporary.is_file() or not temporary.stat().st_size:
            raise AgfError(f"Native renderer failed (exit {result['exit_code']}, timeout={result['timed_out']}): "
                           f"{(result['stdout'] + result['stderr'])[-1500:]}")
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with temporary.open("rb") as src, output.open("xb") as dst:
                shutil.copyfileobj(src, dst)
        except OSError as exc:
            raise AgfError(f"Cannot create render output: {exc}") from exc
    return {"status": "RENDERED", "tool": executable, "output": str(output), "execution": result,
            "input_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def parse_trace(text: str, format: str) -> tuple[list, int]:
    rows, ignored = [], 0
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.match(r"\s*#(\d+)\s+(.+)", line) if format == "gdb" else None
        if format == "gdb" and match:
            rows.append({"line": number, "label": match.group(2)[:500], "raw": line[:2000], "kind": "stack-frame"})
        elif format == "ftrace" and not line.lstrip().startswith("#"):
            function = re.search(r"\|\s*([A-Za-z_][\w:.<>]*)\s*\([^;]*\)\s*(?:\{|;)", line)
            event = re.search(r"\b\d+\.\d+:\s*([\w:]+):?\s*(.*)", line)
            if function or event:
                rows.append({"line": number, "label": (function or event).group(1), "raw": line[:2000], "kind": "trace-record"})
            else:
                ignored += 1
        else:
            ignored += 1
    return rows, ignored


def trace_html(rows: list, format: str, source: str, sha256: str, ignored: int) -> str:
    items = "\n".join(f'<details><summary>line {row["line"]}: {html.escape(row["label"], quote=True)}</summary><pre>{html.escape(row["raw"], quote=True)}</pre></details>' for row in rows)
    return f'''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Trace evidence</title><style>body{{font:16px/1.6 system-ui;max-width:1000px;margin:30px auto;padding:0 20px}}details{{border:1px solid #bbb;padding:10px;margin:8px 0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}input{{padding:8px;width:95%}}</style>
<h1>Trace evidence</h1><p>來源：{html.escape(source, quote=True)}<br>SHA-256: {sha256}<br>Format: {format}; recognized: {len(rows)}; ignored: {ignored}.</p>
<p>這份檢視只呈現已辨識的紀錄。GDB stack 與 ftrace 記錄不代表完整呼叫、時序或因果關係；原始行顯示上限為 2000 字元。</p>
<label>篩選紀錄 <input id="query" type="search"></label><main>{items}</main>
<script>document.getElementById('query').addEventListener('input',function(){{let q=this.value.toLowerCase();document.querySelectorAll('details').forEach(e=>e.hidden=!e.textContent.toLowerCase().includes(q));}});</script></html>'''


def _trace(args):
    if args.limit < 1:
        raise AgfError("limit must be positive")
    source = Path(args.input)
    if source.stat().st_size > 20_000_000:
        raise AgfError("Trace exceeds 20 MB; first select a relevant log slice")
    raw = source.read_bytes()
    rows, ignored = parse_trace(raw.decode("utf-8", errors="replace"), args.format)
    if not rows:
        raise AgfError("No recognized trace records; refusing a misleading empty visualization")
    sha = hashlib.sha256(raw).hexdigest()
    if args.output:
        write_text(args.output, trace_html(rows, args.format, str(source), sha, ignored))
    return {"status": "CREATED" if args.output else "PREVIEW", "output": args.output, "source": str(source),
            "source_sha256": sha, "records": len(rows), "ignored_nonblank_lines": ignored,
            "rows": rows[:args.limit], "truncated": len(rows) > args.limit,
            "limitation": "A searchable record view; not proof of complete execution or causal relationships."}


def register(subparsers):
    parser = subparsers.add_parser("diagram", help="Create diagrams and inspect observed traces")
    commands = parser.add_subparsers(dest="diagram_operation", required=True)
    create = commands.add_parser("create")
    create.add_argument("input")
    create.add_argument("--format", choices=["mermaid", "drawio"], required=True)
    create.add_argument("--output")
    create.set_defaults(func=_create)
    validate = commands.add_parser("validate")
    validate.add_argument("input")
    validate.add_argument("--format", choices=["mermaid", "drawio"], required=True)
    validate.set_defaults(func=_validate)
    render = commands.add_parser("render")
    render.add_argument("input")
    render.add_argument("--format", choices=["mermaid", "drawio"], required=True)
    render.add_argument("--output", required=True)
    render.add_argument("--tool")
    render.add_argument("--tool-arg", action="append", default=[], help="Argument before renderer flags; e.g. the JS entrypoint when --tool is node.exe")
    render.add_argument("--timeout", type=int, default=60)
    render.add_argument("--execute", action="store_true")
    render.set_defaults(func=_render)
    trace = commands.add_parser("trace")
    trace.add_argument("input")
    trace.add_argument("--format", choices=["gdb", "ftrace"], required=True)
    trace.add_argument("--output")
    trace.add_argument("--limit", type=int, default=30)
    trace.set_defaults(func=_trace)
