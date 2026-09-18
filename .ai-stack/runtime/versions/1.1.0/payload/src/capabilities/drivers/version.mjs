import { execFile as execFileCallback } from "node:child_process";
import { promisify } from "node:util";

import { isNormalizedSemver, parseExecutableVersion } from "../version-parser.mjs";

const execFile = promisify(execFileCallback);

function targetCommand(targetId) {
  if (targetId === "node-version") return { executable: process.execPath, args: ["--version"] };
  if (targetId === "slow-node-version") {
    return { executable: process.execPath, args: ["-e", "setTimeout(() => {}, 1000)"] };
  }
  return undefined;
}

export function isSupportedNodeVersion(version) {
  if (!isNormalizedSemver(version)) return false;
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
      const version = parseExecutableVersion(result?.version ?? "", check.config?.["version-parsing"]);
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
    const version = parseExecutableVersion(result.stdout);
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
