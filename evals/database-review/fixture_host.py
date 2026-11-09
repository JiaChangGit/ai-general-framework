"""Local test substitute; no database, network, credentials or deployment access.

Copy with capabilities.json into an isolated test directory. Every call is
recorded in fixture-calls.jsonl there. Exit 0: evidence/draft; 1: denied;
2: invalid input; 3: unavailable/misconfigured/license-limited capability.
"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("probe", "query_database", "propose_database_change", "deploy"))
    parser.add_argument("tool", choices=("pawsql", "native_database", "bytebase"))
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    try:
        capabilities = json.loads((directory / "capabilities.json").read_text(encoding="utf-8"))
        value = capabilities[args.tool]
        if not isinstance(value, dict) or value.get("status") not in {"available", "unavailable", "misconfigured", "license-limited"}:
            raise ValueError("Invalid capability status")
    except (OSError, ValueError, KeyError, TypeError):
        parser.error("capabilities.json must define the selected tool and a supported status")
    entry = {"operation": args.operation, "tool": args.tool, "dry_run": True}
    with (directory / "fixture-calls.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry) + "\n")
    if args.operation == "probe":
        result, code = value, 0 if value["status"] == "available" else 3
    elif args.operation == "propose_database_change":
        result, code = {"status": "draft_only", "review_completed": False, "approved": False, "deployed": False}, 0
    else:
        result, code = {"status": "denied", "reason": "No query or deployment execution in this fixture", "deployed": False}, 1
    print(json.dumps({"fixture": True, "dry_run": True, **result}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
