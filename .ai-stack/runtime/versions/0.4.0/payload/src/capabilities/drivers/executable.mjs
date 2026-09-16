import { execFile as execFileCallback } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const EXACT_VERSION = /^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;

function targetExecutable(projectRoot, targetId) {
  if (targetId === "node-executable") return { executable: process.execPath, args: ["--version"] };
  if (targetId === "missing-executable") {
    return { executable: path.join(projectRoot, ".ai-stack", "capabilities", "missing-executable"), args: ["--version"] };
  }
  return undefined;
}

function parseVersion(output) {
  const version = output.trim().replace(/^v/, "");
  if (!EXACT_VERSION.test(version)) throw new Error("invalid version");
  return version;
}

export async function observeCheck({ check, projectRoot, allowedEffects, signal }) {
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  const target = targetExecutable(projectRoot, check.targetId);
  if (!target) return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  try {
    const result = await execFile(target.executable, target.args, {
      shell: false,
      timeout: check.timeoutMs,
      maxBuffer: 256 * 1024,
      windowsHide: true,
      signal
    });
    const evidence = { present: true };
    if (check.evidence.fields.some(({ name }) => name === "version")) {
      evidence.version = parseVersion(result.stdout);
    }
    return { status: "pass", evidence };
  } catch (error) {
    if (error?.code === "ETIMEDOUT" || error?.code === "ABORT_ERR" || error?.killed) {
      return { status: "unknown", evidence: {}, reasonCode: "CHECK_TIMEOUT" };
    }
    if (error?.code === "ENOENT") return { status: "fail", evidence: {}, reasonCode: "TARGET_MISSING" };
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  }
}
