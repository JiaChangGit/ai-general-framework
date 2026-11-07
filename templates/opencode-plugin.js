// 審閱後才放入目標專案 .opencode/plugins/agf-quick-check.js；此範本不會自行啟用。
// 官方 API（2026-11-08）：https://opencode.ai/docs/build/plugins/server
// V2 使用 id/setup + ctx.tool.hook；V1 的 object/server 入口需 1.18.29+。
// 僅觀察成功的 edit/write。shell、patch、其他工具及外部編輯不在涵蓋範圍；
// 完整提交/CI 檢查仍由同一個 Python check 命令負責。這不是權限隔離機制。
// 只依賴 Node built-ins。需要 Python 3.11+；AGF_PYTHON 可指定真正的 executable。
import { execFile } from "node:child_process";
import { stat } from "node:fs/promises";
import { join, resolve } from "node:path";
import { promisify } from "node:util";

const execute = promisify(execFile);
const edited = new Set(["edit", "write"]);

function checker(root) {
  return join(root, ".agf", "managed", "runtime", "scripts", "agf.py");
}

async function isFile(path) {
  try {
    return (await stat(path)).isFile();
  } catch {
    return false;
  }
}

function reporter(input) {
  return async (result) => {
    const level = result.status === "PASS" ? "info" : result.status === "FAIL" ? "error" : "warn";
    const message = `[agf quick-check] ${JSON.stringify(result)}`;
    // V1 exposes client.app.log. V2's documented server examples use console;
    // neither path creates a user prompt or edits the model's conversation.
    if (typeof input?.client?.app?.log === "function") {
      try {
        await input.client.app.log({ body: { service: "agf", level, message } });
        return;
      } catch {
        // A missing/rejected log endpoint must not hide the check outcome.
      }
    }
    console.error(message);
  };
}

function quickCheck(rootValue, input) {
  const root = rootValue ? resolve(rootValue) : null;
  const log = reporter(input);
  return async (tool) => {
    const finish = async (result) => {
      await log({ ...result, tool });
      return result;
    };
    if (!root) return finish({ status: "SKIP", reason: "Project directory is unavailable; no check ran." });
    const script = checker(root);
    const config = join(root, ".agf", "quality.json");
    if (!(await isFile(script))) return finish({ status: "SKIP", reason: "Managed Python runtime is missing; run project install after review.", path: script });
    if (!(await isFile(config))) return finish({ status: "SKIP", reason: "Project quality config is missing; review and configure actual quick checks first.", path: config });
    const python = process.env.AGF_PYTHON || (process.platform === "win32" ? "python" : "python3");
    if (/\.(cmd|bat)$/i.test(python)) return finish({ status: "SKIP", reason: "AGF_PYTHON must name a real executable, not a batch shim." });
    const argv = ["-X", "utf8", script, "check", "--root", root, "--config", config, "--profile", "quick"];
    try {
      const { stdout } = await execute(python, argv, {
        cwd: root, shell: false, windowsHide: true,
        encoding: "utf8", timeout: 240000, maxBuffer: 262144,
      });
      let data;
      try { data = JSON.parse(stdout); } catch { /* Report a non-AGF executable without claiming PASS. */ }
      if (data?.status !== "PASS" || !Array.isArray(data.checks) || data.checks.length === 0) {
        return finish({ status: "FAIL", reason: "Checker returned no successful nonempty check result.", exit_code: 0 });
      }
      return finish({ status: "PASS", exit_code: 0, checks: data.checks.map((check) => ({ name: check.name, status: check.status })) });
    } catch (error) {
      return finish({ status: error.code === "ENOENT" ? "SKIP" : "FAIL",
        reason: error.code === "ENOENT" ? "Python was not found; set AGF_PYTHON to an installed Python 3.11+ executable." : "Quick checks failed or exceeded their execution/output limit; inspect the same check command manually.",
        exit_code: typeof error.code === "number" ? error.code : null,
        error_code: typeof error.code === "string" ? error.code : null });
    }
  };
}

export default {
  id: "agf.quick-check",

  // Current V2 API. Scope this local plugin to its attached project, not global
  // sessions. A copied plugin in another checkout uses that checkout's runtime.
  async setup(ctx) {
    const run = quickCheck(ctx.location?.directory || ctx.location?.project?.directory, null);
    await ctx.tool.hook("execute.after", async (event) => {
      if (event.status === "completed" && edited.has(event.tool)) await run(event.tool);
    });
  },

  // Documented V1 object API (>= 1.18.29); older function-only loaders need a
  // version-specific adaptation. V2 ignores this server() implementation.
  async server(input) {
    const run = quickCheck(input.worktree || input.directory, input);
    return {
      "tool.execute.after": async (event) => {
        if (edited.has(event.tool)) await run(event.tool);
      },
    };
  },
};
