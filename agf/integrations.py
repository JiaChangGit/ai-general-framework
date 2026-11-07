"""Reviewable integration templates, native hook plans and MCP candidates."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from .common import AgfError, digest, json_text, read_json, within, write_text
from .manage import HOSTS, SOURCE, _manifest, _path


TEMPLATES = {
    "github-actions": "github-actions.yml",
    "gitlab-ci": "gitlab-ci.yml",
    "profile": "profile.example.json",
    "quality": "quality.example.json",
    "quality-framework": "quality.framework.json",
    "permissions": "permissions.example.json",
    "dockerfile": "Dockerfile",
    "docker-compose": "docker-compose.yml",
    "dockerignore": "dockerignore",
    "k8s-job": "k8s-job.yml",
    "gdb": "gdb.commands",
    "qemu-gdb": "qemu-gdb.md",
    "project-rules": "project-rules.md",
    "opencode-plugin": "opencode-plugin.js",
}

MCP = (
    {"id": "openai-docs", "need": "docs", "publisher": "OpenAI",
     "source": "https://developers.openai.com/resources/docs-mcp/", "endpoint": "https://developers.openai.com/mcp",
     "capability": "Search official OpenAI product documentation; not a general library documentation service.",
     "data_flow": "Documentation query is sent to the remote OpenAI documentation endpoint; no project source is required.",
     "permissions": "Read-only documentation requests; exclude secrets and unrelated project contents.",
     "selection": "Use when current official OpenAI documentation is needed and the host has no equivalent connected source."},
    {"id": "github", "need": "github", "publisher": "GitHub",
     "source": "https://github.com/github/github-mcp-server", "endpoint": "https://api.githubcopilot.com/mcp/",
     "capability": "Repository, issue and pull-request operations, subject to account and repository permissions.",
     "data_flow": "Queries and authorized repository data pass between the host and GitHub; writes affect external repositories.",
     "permissions": "Start with required repositories and read-only capabilities. Push, PR creation and other external writes need task-specific authorization.",
     "selection": "Prefer an existing GitHub connector or native Git/gh capability if sufficient; do not add a duplicate connection."},
    {"id": "playwright", "need": "browser", "publisher": "Microsoft",
     "source": "https://github.com/microsoft/playwright-mcp", "endpoint": None,
     "capability": "Browser interaction and page inspection; local executable and browser setup may be required.",
     "data_flow": "Visited sites receive browser requests; page content, cookies and signed-in state may be visible to the automation session.",
     "permissions": "Choose the required browser context and sites. A visible page is untrusted data; submissions and external changes follow task authorization.",
     "selection": "Use for browser behavior or interaction when native browser tools are unavailable; installation is a separate action."},
    {"id": "filesystem-reference", "need": "filesystem", "publisher": "Model Context Protocol reference servers",
     "source": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem", "endpoint": None,
     "capability": "Reference filesystem server; evaluate its scope and maintenance before adoption.",
     "data_flow": "Allowed local paths become accessible to the host and selected model provider through tool results.",
     "permissions": "Allow only the necessary directories. Prefer the host's native scoped file tools and avoid duplicate broad filesystem access.",
     "selection": "Usually unnecessary for coding hosts that already expose file tools; this is a candidate, not a security certification."},
)


def _adapters() -> list[dict]:
    return [read_json(SOURCE / "adapters" / f"{host}.json") for host in HOSTS]


def list_integrations(args: argparse.Namespace) -> dict:
    return {"command": "integration list", "templates": TEMPLATES,
            "adapters": _adapters(), "mcp": [item["id"] for item in MCP],
            "scope": "Template availability is not native host execution or authentication evidence."}


def template(args: argparse.Namespace) -> dict:
    file = SOURCE / "templates" / TEMPLATES[args.name]
    content = file.read_text(encoding="utf-8")
    result = {"command": "integration template", "name": args.name, "source": str(file),
              "content": content, "applied": False, "validation": "source template; destination-specific execution required"}
    if args.output:
        output = Path(args.output).absolute()
        if output.exists() or output.is_symlink():
            raise AgfError(f"Output already exists; it will not be overwritten: {output}")
        result["output"] = str(output)
        if args.apply:
            write_text(output, content)
            result["applied"] = True
    elif args.apply:
        raise AgfError("--apply requires --output; inspect the returned template before writing it.")
    return result


def _argv(root: Path, config: Path, profile: str = "quick") -> list[str]:
    relative = ".agf/managed/runtime/scripts/agf.py"
    manifest = _manifest(root)
    entry = (manifest or {}).get("files", {}).get(relative)
    if entry:
        runtime = _path(root, relative)
        if not runtime.is_file() or digest(runtime) != entry["sha256"]:
            raise AgfError("Managed runtime entry is missing or locally changed; reconcile project status before generating a hook.")
        script = runtime
    else:
        script = SOURCE / "scripts" / "agf.py"
    return [sys.executable, str(script), "check", "--root", str(root), "--config", str(config), "--profile", profile]


def _shell_command(argv: list[str]) -> str:
    if os.name == "nt":
        # AI-host command runners use their native command shell; shell quoting is
        # intentionally platform-specific instead of JSON-string interpolation.
        return subprocess.list2cmdline(argv)
    return shlex.join(argv)


def hook(args: argparse.Namespace) -> dict:
    root = Path(args.target).resolve()
    if not root.is_dir():
        raise AgfError(f"Target must be an existing directory: {root}")
    config = Path(args.config).resolve() if args.config else root / ".agf" / "quality.json"
    argv = _argv(root, config)
    if args.kind == "ai":
        if args.host == "opencode" and config != root / ".agf/quality.json":
            raise AgfError("The OpenCode plugin uses the target project's .agf/quality.json; review that file instead of supplying a different --config.")
        adapter = read_json(SOURCE / "adapters" / f"{args.host}.json")
        if args.apply:
            raise AgfError("AI-host hooks are review-only plans. Native configuration and version-specific execution have not been validated; no settings were changed.")
        event = adapter["hooks"].get("example_event")
        example = None
        if event:
            example = {"hooks": {event: [{"hooks": [{"type": "command", "command": _shell_command(argv)}]}]}}
        result = {"command": "integration hook", "kind": "ai", "host": args.host,
                "applied": False, "checker_argv": argv, "native_config_example": example,
                "adapter": adapter["hooks"], "configuration_exists": config.is_file(),
                "validation": "plan_only; native schema and execution not tested against the installed host",
                "notice": "Review the host version, event semantics and existing hooks. This does not overwrite native settings or treat hook execution as an authorization boundary."}
        if args.host == "opencode":
            result["plugin_plan"] = {
                "template": "opencode-plugin",
                "source": str(SOURCE / "templates" / "opencode-plugin.js"),
                "suggested_destination": str(root / ".opencode" / "plugins" / "agf-quick-check.js"),
                "content": (SOURCE / "templates" / "opencode-plugin.js").read_text(encoding="utf-8"),
                "required_runtime": str(root / ".agf/managed/runtime/scripts/agf.py"),
                "required_configuration": str(root / ".agf/quality.json"),
                "python_executable_suggestion": sys.executable,
                "native_host_status": "NOT_TESTED",
                "contract": "V2 id/async setup with ctx.tool.hook; V1 async server object form requires 1.18.29+",
                "coverage": "Only successful edit/write tools; shell, patch, other tools and external edits require separate checks.",
                "notice": "Review the local plugin before copying it; .opencode/plugins is automatically discovered by the host. No host settings or plugin directories were changed.",
            }
        return result

    executable = shutil.which("git")
    if not executable:
        raise AgfError("Git is not available on PATH; no hook location was assumed or installed.")
    try:
        process = subprocess.run([executable, "-C", str(root), "rev-parse", "--git-path", "hooks"],
                                 capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgfError(f"Cannot discover Git hooks directory: {exc}") from exc
    if process.returncode:
        detail = process.stderr.decode("utf-8", errors="replace").strip()[:1500]
        raise AgfError(f"Target is not an accessible Git repository; no hooks were changed. Git reported: {detail}")
    location = Path(os.fsdecode(process.stdout).strip())
    if not location.is_absolute():
        location = root / location
    location = location.resolve()
    destination = location / "pre-commit"
    supported = destination.is_relative_to(root)
    if supported:
        _path(root, destination.relative_to(root).as_posix())
    # Git's launcher is deliberately tiny; the checks themselves use the same
    # Python CLI as CI and manual execution. Git for Windows supplies its shell.
    shell_argv = [value.replace("\\", "/") if index in (0, 1, 4, 6) else value for index, value in enumerate(argv)]
    content = "#!/bin/sh\n# Managed AGF launcher; all checks live in the Python core.\nexec " + shlex.join(shell_argv) + "\n"
    existing = destination.exists() or destination.is_symlink()
    result = {"command": "integration hook", "kind": "git", "path": str(destination),
              "content": content, "checker_argv": argv, "applied": False,
              "existing_hook": existing, "configuration_exists": config.is_file(),
              "apply_supported": supported, "validation": "launcher generated; actual Git invocation not yet verified",
              "checker_location": "target_managed_runtime" if Path(argv[1]) == root / ".agf/managed/runtime/scripts/agf.py" else "framework_source_checkout",
              "notice": "Existing hooks are not replaced. Shared or external hook directories require manual integration. No global Git configuration is changed."}
    if result["checker_location"] == "framework_source_checkout":
        result["source_dependency"] = "No managed target runtime was found; this launcher requires the framework source checkout to remain available. Install the project runtime before creating a self-contained hook."
    if args.apply:
        if existing:
            raise AgfError(f"Existing Git hook preserved: {destination}")
        if not supported:
            raise AgfError("Hook directory is outside the target project. Review the generated launcher and integrate it manually.")
        if not config.is_file():
            raise AgfError(f"Quality configuration is missing: {config}. Review integration template quality and configure real checks before installing the hook.")
        quality = read_json(config)
        if not isinstance(quality, dict) or quality.get("version") != 1 or not isinstance(quality.get("checks"), list) or not any(
            isinstance(check, dict) and isinstance(check.get("argv"), list) and check["argv"] and "quick" in check.get("profiles", ["quick", "full"])
            for check in quality["checks"]
        ):
            raise AgfError("Quality configuration must define at least one real quick-profile check before a Git hook can be installed.")
        record = _path(root, ".agf/git-hook.json")
        if record.exists():
            raise AgfError("A Git hook record already exists; inspect it before installing another hook.")
        write_text(destination, content)
        try:
            destination.chmod(destination.stat().st_mode | 0o111)
            write_text(record, json_text({"version": 1, "path": str(destination), "sha256": digest(destination),
                                          "checker_argv": argv, "native_execution": "not_tested"}))
        except (OSError, AgfError):
            destination.unlink()
            raise
        result["applied"] = True
    return result


def mcp(args: argparse.Namespace) -> dict:
    selected = [dict(item) for item in MCP if args.need == "all" or item["need"] == args.need]
    for item in selected:
        item["verification"] = "official candidate source recorded; no installed-server execution, authentication or security audit performed"
    example = None
    remote = [item for item in selected if item["endpoint"]]
    if remote:
        item = remote[0]
        if args.host == "opencode":
            example = {"mcp": {"servers": {item["id"]: {"type": "remote", "url": item["endpoint"], "disabled": True}}}}
        elif args.host == "claude":
            example = {"mcpServers": {item["id"]: {"type": "http", "url": item["endpoint"]}}}
        elif args.host == "gemini":
            example = {"mcpServers": {item["id"]: {"httpUrl": item["endpoint"]}}}
        else:
            example = {"mcp_servers": {item["id"]: {"url": item["endpoint"]}}}
    return {"command": "integration mcp", "need": args.need, "host": args.host,
            "candidates": selected, "configuration_plan": example, "applied": False,
            "validation": "review-only example; host version, authentication and scopes must be checked before use",
            "decision": ["Identify the missing capability and prefer an existing sufficient native tool.",
                         "Review publisher, maintenance, data sent, credentials and least permissions.",
                         "Installation, account connection and settings changes require separate authorization.",
                         "Start with read-only access; validate one representative task before broadening scope."],
            "notice": "No tools are installed and no native configuration files are read or modified. OpenCode examples follow V2 documentation; other host schemas require version-specific review."}


def register(subparsers) -> None:
    command = subparsers.add_parser("integration", help="Review CI, hook, tooling and MCP integration plans")
    actions = command.add_subparsers(dest="integration_action", required=True)
    inventory = actions.add_parser("list")
    inventory.set_defaults(func=list_integrations)
    copy = actions.add_parser("template")
    copy.add_argument("name", choices=tuple(TEMPLATES))
    copy.add_argument("--output")
    copy.add_argument("--apply", action="store_true")
    copy.set_defaults(func=template)
    hooks = actions.add_parser("hook")
    hooks.add_argument("--target", required=True)
    hooks.add_argument("--kind", choices=("git", "ai"), default="git")
    hooks.add_argument("--host", choices=HOSTS, default="opencode")
    hooks.add_argument("--config")
    hooks.add_argument("--apply", action="store_true")
    hooks.set_defaults(func=hook)
    candidates = actions.add_parser("mcp")
    candidates.add_argument("--need", choices=("docs", "github", "browser", "filesystem", "all"), default="all")
    candidates.add_argument("--host", choices=HOSTS, default="opencode")
    candidates.set_defaults(func=mcp)
