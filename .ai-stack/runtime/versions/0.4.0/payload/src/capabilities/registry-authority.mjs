import path from "node:path";

import { CapabilityError } from "./errors.mjs";
import { assertSafeTarget, DEFAULT_FILE_SYSTEM } from "./safe-paths.mjs";

const DESCRIPTOR_PATH = path.join("runtime", "capabilities", "driver-registry.json");
const DRIVER_MODULES = Object.freeze({
  executable: "src/capabilities/drivers/executable.mjs",
  version: "src/capabilities/drivers/version.mjs",
  "file-config": "src/capabilities/drivers/file-config.mjs",
  mcp: "src/capabilities/drivers/mcp.mjs",
  authentication: "src/capabilities/drivers/authentication.mjs",
  network: "src/capabilities/drivers/network.mjs"
});
const DRIVER_IDS = Object.freeze(Object.keys(DRIVER_MODULES));

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value, expected) {
  const keys = Object.keys(value);
  return keys.length === expected.length && keys.every((key) => expected.includes(key));
}

function validateDescriptor(descriptor) {
  if (!isRecord(descriptor) || !exactKeys(descriptor, ["schemaVersion", "drivers"])
    || descriptor.schemaVersion !== 1 || !Array.isArray(descriptor.drivers)
    || descriptor.drivers.length !== DRIVER_IDS.length) return false;
  const seen = new Set();
  return descriptor.drivers.every((driver, index) => {
    if (!isRecord(driver) || !exactKeys(driver, ["id", "module"])
      || driver.id !== DRIVER_IDS[index]
      || driver.module !== DRIVER_MODULES[driver.id]
      || seen.has(driver.id)) return false;
    seen.add(driver.id);
    return true;
  });
}

export async function loadDriverRegistryDescriptor({ payloadRoot, fileSystem = DEFAULT_FILE_SYSTEM } = {}) {
  try {
    if (typeof payloadRoot !== "string" || payloadRoot.length === 0) throw new Error("payload root required");
    const descriptorPath = path.join(payloadRoot, DESCRIPTOR_PATH);
    fileSystem = { ...DEFAULT_FILE_SYSTEM, ...fileSystem };
    await assertSafeTarget(descriptorPath, fileSystem);
    const entry = await fileSystem.lstat(descriptorPath);
    if (entry.isSymbolicLink() || !entry.isFile()) throw new Error("invalid descriptor");
    const descriptor = JSON.parse((await fileSystem.readFile(descriptorPath)).toString("utf8"));
    if (!validateDescriptor(descriptor)) throw new Error("invalid descriptor");
    return structuredClone(descriptor);
  } catch {
    throw new CapabilityError("DRIVER_FAILURE");
  }
}

export function driverModuleForId(driverId) {
  return DRIVER_MODULES[driverId];
}

export function driverRegistryIds() {
  return [...DRIVER_IDS];
}
