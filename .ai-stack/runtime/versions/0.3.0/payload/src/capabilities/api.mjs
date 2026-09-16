import { loadCapabilityCatalog } from "./catalog.mjs";
import { executeDeclaredRepair } from "./repair-executor.mjs";
import { loadDriverRegistry } from "./driver-registry.mjs";
import { createProductiveBindingProvider } from "./bindings.mjs";
import { verifyCapabilityRuntime } from "./runtime.mjs";
import { runDoctor } from "./doctor.mjs";
import { runPreflight } from "./preflight.mjs";
import { CapabilityError } from "./errors.mjs";

const PREFLIGHT_OPTIONS = new Set(["tasks", "surfaces", "allowedEffects", "now"]);
const DOCTOR_OPTIONS = new Set(["capability", "surface", "task", "allowedEffects", "deep", "nativeAuth", "now"]);
const REPAIR_OPTIONS = new Set(["now"]);

function publicOptions(options, allowed) {
  if (!options || typeof options !== "object" || Array.isArray(options)) {
    throw new Error("invalid options");
  }
  if (Object.keys(options).some((key) => !allowed.has(key))) {
    throw new Error("invalid options");
  }
  return { ...options };
}

async function verifiedCapabilityInputs(projectRoot) {
  const runtime = await verifyCapabilityRuntime(projectRoot);
  const catalog = await loadCapabilityCatalog({ payloadRoot: runtime.payloadRoot });
  const drivers = await loadDriverRegistry({ payloadRoot: runtime.payloadRoot });
  const bindingProvider = createProductiveBindingProvider({ catalog });
  return { runtime, catalog, drivers, bindingProvider };
}

export async function preflightProject(projectRoot, options = { tasks: [] }) {
  let safeOptions;
  try {
    safeOptions = publicOptions(options, PREFLIGHT_OPTIONS);
  } catch {
    throw new CapabilityError("INVALID_CAPABILITY_ARGUMENTS");
  }
  const { runtime, catalog, drivers, bindingProvider } = await verifiedCapabilityInputs(projectRoot);
  return runPreflight({
    projectRoot,
    options: { ...safeOptions, catalog, drivers, bindingProvider, runtimeVersion: runtime.version }
  });
}

export async function doctorProject(projectRoot, options = {}) {
  let safeOptions;
  try {
    safeOptions = publicOptions(options, DOCTOR_OPTIONS);
  } catch {
    throw new CapabilityError("INVALID_CAPABILITY_ARGUMENTS");
  }
  const { runtime, catalog, drivers, bindingProvider } = await verifiedCapabilityInputs(projectRoot);
  return runDoctor({
    projectRoot,
    options: { ...safeOptions, catalog, drivers, bindingProvider, runtimeVersion: runtime.version }
  });
}

export async function executeRepair(projectRoot, { proposal, authorization, ...options } = {}) {
  let safeOptions;
  try {
    safeOptions = publicOptions(options, REPAIR_OPTIONS);
  } catch {
    throw new CapabilityError("INVALID_CAPABILITY_ARGUMENTS");
  }
  const { catalog, drivers } = await verifiedCapabilityInputs(projectRoot);
  return executeDeclaredRepair({
    projectRoot,
    proposal,
    authorization,
    catalog,
    drivers,
    now: safeOptions.now
  });
}
