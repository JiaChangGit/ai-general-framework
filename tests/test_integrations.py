import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import shutil
import sys
import unittest
from unittest.mock import patch

from agf import integrations, manage
from agf.common import AgfError


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix=".agf-integration-test-", dir=integrations.SOURCE)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def hook_args(self, **kwargs):
        return argparse.Namespace(target=str(self.root), config=None, kind="git", host="opencode", apply=False, **kwargs)

    def template_args(self, name="quality", apply=False):
        return argparse.Namespace(name=name, output=str(self.root / "output.json"), apply=apply)

    def git_result(self):
        return subprocess.CompletedProcess([], 0, b".git/hooks\n", b"")

    def framework_fixture(self):
        source = self.root / "fixture-framework"
        shutil.copytree(integrations.SOURCE / "agf", source / "agf", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(integrations.SOURCE / "scripts", source / "scripts")
        (source / "templates").mkdir()
        shutil.copyfile(integrations.SOURCE / "templates/project-rules.md", source / "templates/project-rules.md")
        shutil.copyfile(integrations.SOURCE / "templates/git-hook.py", source / "templates/git-hook.py")
        (source / "docs").mkdir()
        for name in manage.GUIDES:
            (source / "docs" / name).write_text(f"Fixture guide {name}\n", encoding="utf-8")
        skill = source / "skills" / "fixture"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: fixture\ndescription: Isolated test fixture\n---\nUse only fixture files.\n", encoding="utf-8")
        return source

    def install_runtime(self, source, root, tools="copy"):
        manage.project(argparse.Namespace(operation="install", target=str(root), source=str(source), host=["opencode"], skill=["fixture"], tools=tools, apply=True))

    def git_environment(self, root):
        return {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "safe.directory",
                "GIT_CONFIG_VALUE_0": str(root).replace("\\", "/")}

    def test_template_is_read_only_until_apply(self):
        result = integrations.template(self.template_args())
        self.assertFalse(result["applied"])
        self.assertEqual(list(self.root.iterdir()), [])
        written = integrations.template(self.template_args(apply=True))
        self.assertTrue(written["applied"])
        data = json.loads((self.root / "output.json").read_text(encoding="utf-8"))
        self.assertEqual(data["checks"][0]["argv"][0], "{python}")

    def test_template_never_overwrites_output(self):
        (self.root / "output.json").write_text("local content", encoding="utf-8")
        with self.assertRaises(AgfError):
            integrations.template(self.template_args(apply=True))
        self.assertEqual((self.root / "output.json").read_text(encoding="utf-8"), "local content")

    def test_every_catalog_template_exists(self):
        for name, relative in integrations.TEMPLATES.items():
            with self.subTest(name=name):
                self.assertTrue((integrations.SOURCE / "templates" / relative).is_file())
                value = integrations.template(argparse.Namespace(name=name, output=None, apply=False))
                self.assertTrue(value["content"])

    def test_doctor_image_uses_minimal_sources_that_run_independently(self):
        dockerfile = (integrations.SOURCE / "templates/Dockerfile").read_text(encoding="utf-8")
        ignore = integrations.template(argparse.Namespace(name="dockerfile-ignore", output=None, apply=False))["content"]
        rules = [line for line in ignore.splitlines() if line and not line.startswith("#")]
        self.assertEqual(rules, ["**", "!agf/", "!agf/*.py", "!scripts/", "!scripts/agf.py"])
        copies = [line for line in dockerfile.splitlines() if line.startswith("COPY ")]
        self.assertEqual(copies, ["COPY agf/*.py /workspace/agf/", "COPY scripts/agf.py /workspace/scripts/agf.py"])
        # Docker's actual context processing still requires an engine-backed check.
        (self.root / "agf").mkdir()
        (self.root / "scripts").mkdir()
        for source in (integrations.SOURCE / "agf").glob("*.py"):
            shutil.copyfile(source, self.root / "agf" / source.name)
        shutil.copyfile(integrations.SOURCE / "scripts/agf.py", self.root / "scripts/agf.py")
        result = subprocess.run([sys.executable, "-B", str(self.root / "scripts/agf.py"), "doctor"],
                                cwd=self.root, capture_output=True, encoding="utf-8", timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["command"], "doctor")

    def test_framework_quality_uses_real_cli_contract(self):
        value = json.loads(integrations.template(argparse.Namespace(name="quality-framework", output=None, apply=False))["content"])
        self.assertEqual(value["version"], 1)
        self.assertEqual(len(value["checks"]), 2)
        self.assertTrue(all(check["argv"][0] == "{python}" for check in value["checks"]))

    def test_native_host_hook_plans_are_explicitly_not_execution_evidence(self):
        for host in integrations.HOSTS:
            args = self.hook_args()
            args.kind = "ai"
            args.host = host
            value = integrations.hook(args)
            self.assertFalse(value["applied"])
            self.assertEqual(value["adapter"]["execution_status"], "not_tested")
            self.assertIn("check", value["checker_argv"])
            if host == "opencode":
                self.assertEqual(value["plugin_plan"]["native_host_status"], "NOT_TESTED")
                self.assertIn("Only successful edit/write", value["plugin_plan"]["coverage"])
                self.assertIn("execFile", value["plugin_plan"]["content"])
            args.apply = True
            with self.assertRaises(AgfError):
                integrations.hook(args)
        self.assertEqual(list(self.root.iterdir()), [])

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable; OpenCode JS syntax and contract checks are NOT_TESTED")
    def test_opencode_plugin_node_syntax(self):
        result = subprocess.run([shutil.which("node"), "--input-type=module", "--check"],
                                input=(integrations.SOURCE / "templates/opencode-plugin.js").read_text(encoding="utf-8"),
                                capture_output=True, encoding="utf-8", timeout=15, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable; fake-host contract E2E is NOT_TESTED")
    def test_opencode_plugin_contract_executes_real_python_check(self):
        source = self.framework_fixture()
        root = self.root / "target with spaces & $"
        root.mkdir()
        self.install_runtime(source, root)
        quality = {"version": 1, "checks": [{"name": "actual-contract-process", "argv": ["{python}", "-c", "from pathlib import Path; p=Path('runs.txt'); p.write_text(str(int(p.read_text())+1) if p.exists() else '1')"], "cwd": ".", "timeout": 10}]}
        (root / ".agf/quality.json").write_text(json.dumps(quality), encoding="utf-8")
        plugin = self.root / "opencode-plugin.mjs"
        shutil.copyfile(integrations.SOURCE / "templates/opencode-plugin.js", plugin)
        harness = self.root / "contract.mjs"
        harness.write_text(r'''
import assert from "node:assert/strict";
import { readFile, rename, writeFile } from "node:fs/promises";
import { join, parse } from "node:path";
import { pathToFileURL } from "node:url";
const plugin = (await import(pathToFileURL(process.argv[2]).href)).default;
const root = process.argv[3];
const reports = [];
const collect = (message) => reports.push(JSON.parse(message.slice(message.indexOf("{"))));
const client = { app: { log: async ({ body }) => collect(body.message) } };
const v1 = await plugin.server({ directory: root, worktree: root, client });
await v1["tool.execute.after"]({ tool: "read" });
assert.equal(reports.length, 0);
await v1["tool.execute.after"]({ tool: "write" });
await v1["tool.execute.after"]({ tool: "edit" });
assert.equal(reports.filter(x => x.status === "PASS").length, 2);
assert.equal(await readFile(join(root, "runs.txt"), "utf8"), "2");
const callbacks = {};
const previousError = console.error;
console.error = collect;
try {
  await plugin.setup({ location: { directory: root }, tool: { hook: async (name, callback) => { callbacks[name] = callback; } } });
  assert.equal(typeof callbacks["execute.after"], "function");
  await callbacks["execute.after"]({ tool: "write", status: "error" });
  await callbacks["execute.after"]({ tool: "read", status: "completed" });
  assert.equal(reports.length, 2);
  await callbacks["execute.after"]({ tool: "edit", status: "completed" });
  assert.equal(await readFile(join(root, "runs.txt"), "utf8"), "3");
  const manifestPath = join(root, ".agf", "manifest.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  manifest.tools_mode = "shared";
  await writeFile(manifestPath, JSON.stringify(manifest));
  await callbacks["execute.after"]({ tool: "write", status: "completed" });
  assert.equal(reports.at(-1).tools_mode, "shared");
  assert.equal(await readFile(join(root, "runs.txt"), "utf8"), "4");
  const originalSource = manifest.source;
  if (process.platform === "win32") {
    // This still resolves to the real fixture from the current drive/share
    // under Windows Node. Reject it before starting Python or the check.
    manifest.source = "/" + originalSource.slice(parse(originalSource).root.length).replaceAll("\\", "/");
    await writeFile(manifestPath, JSON.stringify(manifest));
    await v1["tool.execute.after"]({ tool: "edit" });
    assert.equal(reports.at(-1).status, "FAIL");
    assert.match(reports.at(-1).reason, /not a native absolute path/);
    assert.equal(await readFile(join(root, "runs.txt"), "utf8"), "4");
  }
  manifest.source = join(root, "missing-source");
  await writeFile(manifestPath, JSON.stringify(manifest));
  await v1["tool.execute.after"]({ tool: "edit" });
  assert.equal(reports.at(-1).status, "FAIL");
  assert.match(reports.at(-1).reason, /Shared tools source is unavailable/);
  assert.equal(await readFile(join(root, "runs.txt"), "utf8"), "4");
  manifest.source = originalSource;
  delete manifest.tools_mode;
  await writeFile(manifestPath, JSON.stringify(manifest));
  await v1["tool.execute.after"]({ tool: "edit" });
  assert.equal(reports.at(-1).tools_mode, "copy");
  assert.equal(await readFile(join(root, "runs.txt"), "utf8"), "5");
  const config = join(root, ".agf", "quality.json");
  await writeFile(config, JSON.stringify({version: 1, checks: [{name: "intentional-failure", argv: [process.env.AGF_PYTHON, "-c", "raise SystemExit(3)"]}]}));
  await callbacks["execute.after"]({ tool: "write", status: "completed" });
  assert.equal(reports.at(-1).status, "FAIL");
  await rename(config, config + ".saved");
  await v1["tool.execute.after"]({ tool: "edit" });
  assert.equal(reports.at(-1).status, "SKIP");
  assert.match(reports.at(-1).reason, /quality config/);
  const script = join(root, ".agf", "managed", "runtime", "scripts", "agf.py");
  await rename(script, script + ".saved");
  await v1["tool.execute.after"]({ tool: "write" });
  assert.equal(reports.at(-1).status, "FAIL");
  assert.match(reports.at(-1).reason, /runtime/);
} finally { console.error = previousError; }
console.log(JSON.stringify({status: "contract_pass", successful_real_checks: reports.filter(x => x.status === "PASS").length, native_host: "NOT_TESTED"}));
''', encoding="utf-8")
        environment = dict(os.environ, AGF_PYTHON=sys.executable)
        result = subprocess.run([shutil.which("node"), str(harness), str(plugin), str(root)],
                                cwd=root, env=environment, capture_output=True, encoding="utf-8", timeout=45, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["successful_real_checks"], 5)
        self.assertEqual(report["native_host"], "NOT_TESTED")

    def test_git_hook_plan_does_not_write_and_uses_shared_checker(self):
        with patch.object(integrations.shutil, "which", return_value="git"), patch.object(integrations.subprocess, "run", return_value=self.git_result()) as runner:
            value = integrations.hook(self.hook_args())
        self.assertIn("scripts", value["checker_argv"][1])
        self.assertIn("check", value["checker_argv"])
        self.assertIn("#!/bin/sh", value["content"])
        self.assertEqual(runner.call_args.kwargs["timeout"], 10)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_git_hook_requires_real_quality_configuration_before_apply(self):
        args = self.hook_args()
        args.apply = True
        with patch.object(integrations.shutil, "which", return_value="git"), patch.object(integrations.subprocess, "run", return_value=self.git_result()):
            with self.assertRaises(AgfError):
                integrations.hook(args)
        self.assertFalse((self.root / ".git").exists())

    def test_git_hook_install_and_existing_hook_preservation(self):
        self.install_runtime(self.framework_fixture(), self.root, tools="shared")
        (self.root / ".agf/quality.json").write_text(json.dumps({"version": 1, "checks": [{"name": "probe", "argv": ["{python}", "-c", "print('ok')"]}]}), encoding="utf-8")
        args = self.hook_args()
        args.apply = True
        with patch.object(integrations.shutil, "which", return_value="git"), patch.object(integrations.subprocess, "run", return_value=self.git_result()):
            value = integrations.hook(args)
            self.assertTrue(value["applied"])
            original = (self.root / ".git/hooks/pre-commit").read_bytes()
            with self.assertRaises(AgfError):
                integrations.hook(args)
        self.assertEqual((self.root / ".git/hooks/pre-commit").read_bytes(), original)
        record = json.loads((self.root / ".agf/git-hook.json").read_text(encoding="utf-8"))
        self.assertEqual(record["native_execution"], "not_tested")

    def test_external_hook_directory_cannot_be_written(self):
        args = self.hook_args()
        args.apply = True
        outside = self.root.parent / (self.root.name + "-outside")
        result = subprocess.CompletedProcess([], 0, str(outside).encode(), b"")
        with patch.object(integrations.shutil, "which", return_value="git"), patch.object(integrations.subprocess, "run", return_value=result):
            with self.assertRaises(AgfError):
                integrations.hook(args)
        self.assertFalse(outside.exists())

    def test_removed_mcp_wrapper_is_not_a_cli_command(self):
        parser = argparse.ArgumentParser()
        integrations.register(parser.add_subparsers(required=True))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(["integration", "mcp"])

    def test_parser_and_adapter_inventory(self):
        parser = argparse.ArgumentParser()
        integrations.register(parser.add_subparsers(required=True))
        args = parser.parse_args(["integration", "list"])
        result = args.func(args)
        self.assertEqual({value["host"] for value in result["adapters"]}, set(integrations.HOSTS))

    @unittest.skipUnless(shutil.which("git"), "Git executable is required for native launcher evidence")
    def test_generated_git_hook_really_runs_the_shared_checker(self):
        root = self.root / "專案 with spaces & $"
        root.mkdir()
        # Ignore user hook configuration and trust only this newly created fixture.
        # In particular, Windows Git sees WSL-owned UNC files as another owner.
        environment = self.git_environment(root)
        with patch.dict(os.environ, environment):
            subprocess.run([shutil.which("git"), "-C", str(root), "init", "--quiet"], check=True, capture_output=True, timeout=15)
            self.install_runtime(self.framework_fixture(), root, tools="shared")
            quality = {"version": 1, "checks": [{"name": "actual-python-process", "argv": ["{python}", "-c", "import sys; print('checked'); sys.exit(0)"], "cwd": ".", "timeout": 10}]}
            (root / ".agf/quality.json").write_text(json.dumps(quality), encoding="utf-8")
            args = self.hook_args()
            args.target = str(root)
            args.apply = True
            integrations.hook(args)
            result = subprocess.run([shutil.which("git"), "-C", str(root), "hook", "run", "pre-commit"], capture_output=True, encoding="utf-8", timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # Git forwards hook stdout to stderr, depending on the Git build.
        self.assertIn('"status": "PASS"', result.stdout + result.stderr)
        self.assertIn("actual-python-process", result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("git"), "Git is required for source-independent installed hook evidence")
    def test_installed_git_hook_survives_source_checkout_move(self):
        source = self.framework_fixture()
        root = self.root / "installed target"
        root.mkdir()
        self.install_runtime(source, root)
        quality = {"version": 1, "checks": [{"name": "source-independent-check", "argv": ["{python}", "-c", "from pathlib import Path; Path('checked.txt').write_text('ran')"], "cwd": ".", "timeout": 10}]}
        (root / ".agf/quality.json").write_text(json.dumps(quality), encoding="utf-8")
        with patch.dict(os.environ, self.git_environment(root)):
            subprocess.run([shutil.which("git"), "-C", str(root), "init", "--quiet"], capture_output=True, check=True, timeout=15)
            args = self.hook_args()
            args.target = str(root)
            args.apply = True
            with patch.object(integrations, "SOURCE", source):
                plan = integrations.hook(args)
            self.assertEqual(plan["checker_location"], "target_managed_runtime")
            moved = self.root / "source-moved"
            self.assertTrue(source.resolve().is_relative_to(self.root.resolve()))
            self.assertTrue(moved.resolve().is_relative_to(self.root.resolve()))
            source.rename(moved)
            result = subprocess.run([shutil.which("git"), "-C", str(root), "-c", "user.name=AGF fixture", "-c", "user.email=fixture@example.invalid", "commit", "--allow-empty", "-m", "Verify source-independent hook"],
                                    capture_output=True, encoding="utf-8", timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(source.exists())
        self.assertEqual((root / "checked.txt").read_text(encoding="utf-8"), "ran")
        self.assertIn("source-independent-check", result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("git"), "Git is required for shared-tools hook evidence")
    def test_shared_git_hook_reads_manifest_each_run_and_never_falls_back(self):
        source = self.framework_fixture()
        root = self.root / "shared target"
        root.mkdir()
        self.install_runtime(source, root, tools="shared")
        quality = {"version": 1, "checks": [{"name": "shared-check", "argv": ["{python}", "-c", "print('shared check ran')"]}]}
        (root / ".agf/quality.json").write_text(json.dumps(quality), encoding="utf-8")
        with patch.dict(os.environ, self.git_environment(root)):
            subprocess.run([shutil.which("git"), "-C", str(root), "init", "--quiet"], check=True, capture_output=True, timeout=15)
            args = self.hook_args()
            args.target, args.apply = str(root), True
            result = integrations.hook(args)
            self.assertEqual(result["checker_location"], "framework_source_checkout")
            command = [shutil.which("git"), "-C", str(root), "hook", "run", "pre-commit"]
            first = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=30)
            self.assertEqual(first.returncode, 0, first.stderr)
            manage.project(argparse.Namespace(operation="update", target=str(root), source=None, host=None, skill=None, tools="copy", apply=True))
            moved = self.root / "source-moved"
            self.assertTrue(source.resolve().is_relative_to(self.root.resolve()))
            self.assertTrue(moved.resolve().is_relative_to(self.root.resolve()))
            source.rename(moved)
            copied = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=30)
            self.assertEqual(copied.returncode, 0, copied.stderr)
            manifest_path = root / ".agf/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["tools_mode"] = "shared"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            failed = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=30)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("No fallback", failed.stdout + failed.stderr)


if __name__ == "__main__":
    unittest.main()
