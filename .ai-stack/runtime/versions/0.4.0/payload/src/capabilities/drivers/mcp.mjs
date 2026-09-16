import { readFile } from "node:fs/promises";
import path from "node:path";

import { observeCheck as observeNetworkCheck } from "./network.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM } from "../safe-paths.mjs";

const registrationFile = "mcp-registration.json";
const MAX_BYTES = 64 * 1024;

async function readRegistration(projectRoot, surface, fileSystem) {
  const target = path.join(projectRoot, ".ai-stack", "capabilities", surface, registrationFile);
  await assertSafeTarget(target, fileSystem);
  const entry = await fileSystem.lstat(target);
  if (entry.isSymbolicLink() || !entry.isFile()) throw new Error("invalid registration");
  const bytes = await readFile(target);
  if (bytes.byteLength > MAX_BYTES) throw new Error("bounded registration required");
  return JSON.parse(bytes.toString("utf8"));
}

export async function observeCheck({ check, projectRoot, surface, allowedEffects, signal, fileSystem = DEFAULT_FILE_SYSTEM, bindingHandle, invokeBindingHandle }) {
  fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
  if (!allowedEffects.includes(check.effect)) {
    return { status: "unknown", evidence: {}, reasonCode: "EFFECT_NOT_PERMITTED" };
  }
  if (check.primitiveId === "mcp-live") {
    if (typeof invokeBindingHandle !== "function" || bindingHandle === undefined) {
      return { status: "unknown", evidence: {}, reasonCode: "CAPABILITY_BINDING_UNKNOWN" };
    }
    try {
      const result = await invokeBindingHandle(bindingHandle, "probe", { signal });
      if (!result || typeof result.reachable !== "boolean" || Object.keys(result).some((key) => key !== "reachable")) {
        return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
      }
      return {
        status: result.reachable ? "pass" : "fail",
        evidence: { reachable: result.reachable }
      };
    } catch (error) {
      if (error?.code === "ETIMEDOUT" || error?.code === "ABORT_ERR" || error?.killed) {
        return { status: "unknown", evidence: {}, reasonCode: "CHECK_TIMEOUT" };
      }
      return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
    }
  }
  if (check.targetId === "mcp-registration") {
    try {
      const registration = await readRegistration(projectRoot, surface, fileSystem);
      if (typeof registration.registered !== "boolean") throw new Error("invalid registration");
      return {
        status: registration.registered ? "pass" : "fail",
        evidence: { registered: registration.registered }
      };
    } catch (error) {
      if (error?.code === "ENOENT") return { status: "fail", evidence: {}, reasonCode: "TARGET_MISSING" };
      return { status: "fail", evidence: {}, reasonCode: "TARGET_INVALID" };
    }
  }
  if (check.targetId !== "context7-endpoint" || !allowedEffects.includes("network-read")) {
    return { status: "unknown", evidence: {}, reasonCode: "DRIVER_FAILURE" };
  }
  return observeNetworkCheck({ check, projectRoot, surface, allowedEffects, signal });
}
