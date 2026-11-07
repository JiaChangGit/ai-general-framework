"""The CLI only dispatches helpers; it does not call or select AI models."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .common import AgfError, json_text


def parser():
    result = argparse.ArgumentParser(prog="agf", description="Portable engineering and learning helpers. No installation or model calls on startup.")
    result.add_argument("--version", action="version", version=__version__)
    children = result.add_subparsers(dest="command", required=True)
    from . import audit, context, diagrams, evidence, execution, files, gittools, integrations, manage, profiles, sources
    for module in (manage, profiles, integrations, context, execution, evidence, gittools, files, diagrams, sources, audit):
        module.register(children)
    return result


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        result = args.func(args)
        if result is None:
            result = {"status": "DONE"}
        if not isinstance(result, dict):
            result = {"result": result}
        code = result.pop("_exit_code", 0)
        sys.stdout.write(json_text(result))
        return code
    except (AgfError, OSError, UnicodeError, ValueError) as exc:
        sys.stdout.write(json_text({"status": "ERROR", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
