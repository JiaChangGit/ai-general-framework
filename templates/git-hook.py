"""Embedded by the Git launcher; read the one project manifest on every run."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

root, config = (Path(value).resolve() for value in sys.argv[1:3])
try:
    manifest = json.loads((root / ".agf/manifest.json").read_text(encoding="utf-8"))
    mode = manifest.get("tools_mode", "copy")
    if mode == "shared":
        source = Path(manifest["source"])
        if not source.is_absolute():
            raise ValueError("Shared source path is not native to this environment; no path conversion was attempted.")
        script = source / "scripts/agf.py"
    elif mode == "copy":
        relative = ".agf/managed/runtime/scripts/agf.py"
        script = root / relative
        expected = manifest["files"][relative]["sha256"]
        if hashlib.sha256(script.read_bytes()).hexdigest() != expected:
            raise ValueError("Managed tools entry changed; inspect project status before continuing.")
    else:
        raise ValueError("Unknown tools mode in project manifest.")
    if not script.is_file():
        raise ValueError(f"{mode} tools entry is unavailable: {script}; restore the source or explicitly update --source/--tools. No fallback was attempted.")
except (OSError, ValueError, KeyError, TypeError) as exc:
    print(f"AGF hook cannot select project tools: {exc}", file=sys.stderr)
    raise SystemExit(2)

sys.argv = [str(script), "check", "--root", str(root), "--config", str(config), "--profile", "quick"]
runpy.run_path(str(script), run_name="__main__")
