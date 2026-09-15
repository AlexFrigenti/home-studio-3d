import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const EXACT_VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;

function targetCommand(targetId) {
  if (targetId === "node-version") return { executable: process.execPath, args: ["--version"] };
  if (targetId === "slow-node-version") {
    return { executable: process.execPath, args: ["-e", "setTimeout(() => {}, 1000)"] };
  }
  return undefined;
}

function parseVersion(output) {
  const version = output.trim().replace(/^v/, "");
  if (!EXACT_VERSION.test(version)) throw new Error("invalid version");
  return version;
}

export function isSupportedNodeVersion(version) {
  if (!EXACT_VERSION.test(version)) return false;
  const [major, minor] = version.split(".").map(Number);
  return major === 22 && minor >= 13;
}

export async function observeCheck({ check, allowedEffects, signal, bindingHandle, invokeBindingHandle }) {
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  if (check.primitiveId === "executable-version") {
    if (typeof invokeBindingHandle !== "function" || bindingHandle === undefined) {
      return { status: "unknown", evidence: {}, reasonCode: "CAPABILITY_BINDING_UNKNOWN" };
    }
    try {
      const result = await invokeBindingHandle(bindingHandle, "readVersion", {
        timeoutMs: check.timeoutMs,
        signal
      });
      const version = parseVersion(result?.version ?? "");
      return { status: "pass", evidence: { version } };
    } catch (error) {
      if (error?.code === "ETIMEDOUT" || error?.code === "ABORT_ERR" || error?.killed) {
        return { status: "unknown", evidence: {}, reasonCode: "CHECK_TIMEOUT" };
      }
      return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
    }
  }
  const target = targetCommand(check.targetId);
  if (!target) return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  try {
    const result = await execFile(target.executable, target.args, {
      shell: false,
      timeout: check.timeoutMs,
      maxBuffer: 256 * 1024,
      windowsHide: true,
      signal
    });
    const version = parseVersion(result.stdout);
    if (check.targetId === "node-version" && !isSupportedNodeVersion(version)) {
      return { status: "fail", evidence: { version }, reasonCode: "VERSION_MISMATCH" };
    }
    return { status: "pass", evidence: { version } };
  } catch (error) {
    if (error?.code === "ETIMEDOUT" || error?.code === "ABORT_ERR" || error?.killed) {
      return { status: "unknown", evidence: {}, reasonCode: "CHECK_TIMEOUT" };
    }
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  }
}
