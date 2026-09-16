import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";

import { BootstrapError } from "../bootstrap/errors.mjs";
import { inspectProject } from "../bootstrap/inspect-project.mjs";
import { resolveProjectRelativePath } from "../bootstrap/paths.mjs";
import { loadBootstrapSchemaValidators } from "../bootstrap/schema.mjs";
import { CapabilityError } from "./errors.mjs";
import { resolveCapability } from "./catalog.mjs";
import { loadCapabilityValidators } from "./schema.mjs";

const MANIFEST_PATH = ".ai-stack/manifest.json";

function deepFreeze(value) {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value)) deepFreeze(child);
  }
  return value;
}

function clone(value) {
  return structuredClone(value);
}

function digestBytes(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function mapBootstrapError(error) {
  if (!(error instanceof BootstrapError)) return undefined;
  if (error.code === "MISSING_CAPABILITY_DEFINITIONS") return new CapabilityError("CAPABILITY_DEFINITIONS_MISSING");
  if (error.code === "INVALID_CAPABILITY_DEFINITIONS") return new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  return new CapabilityError("CAPABILITY_REQUIREMENT_INVALID");
}

function copyRequirement(requirement) {
  return clone(requirement);
}

function collectTaskIds(requirements) {
  const taskIds = [];
  const seenTaskIds = new Set();
  for (const requirement of requirements) {
    if (requirement.activation === "always") continue;
    for (const taskId of requirement.activation.tasks) {
      if (!seenTaskIds.has(taskId)) {
        seenTaskIds.add(taskId);
        taskIds.push(taskId);
      }
    }
  }
  return taskIds;
}

export async function loadProjectCapabilityDefinitions(projectRoot) {
  try {
    const inspected = await inspectProject(projectRoot);
    if (inspected.capabilityDefinitions === undefined) return undefined;

    const definitionPath = resolveProjectRelativePath(projectRoot, inspected.capabilityDefinitions);
    let bytes;
    try {
      bytes = await readFile(definitionPath);
    } catch (error) {
      if (error?.code === "ENOENT") throw new CapabilityError("CAPABILITY_DEFINITIONS_MISSING");
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }

    let payload;
    try {
      payload = JSON.parse(bytes.toString("utf8"));
    } catch {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
    const validators = await loadCapabilityValidators();
    if (!validators.validateProjectCapabilityDefinitions(payload)) {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
    return deepFreeze({
      reference: ".ai-stack/capabilities.json",
      fileDigest: digestBytes(bytes),
      capabilities: clone(payload.capabilities)
    });
  } catch (error) {
    const bootstrapFailure = mapBootstrapError(error);
    if (bootstrapFailure) throw bootstrapFailure;
    if (error instanceof CapabilityError) throw error;
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
}

export async function loadProjectCapabilityInputs(projectRoot, { catalog, resolveRequirements = true } = {}) {
  try {
    const inspected = await inspectProject(projectRoot);
    const manifestPath = path.join(projectRoot, MANIFEST_PATH);
    const manifest = JSON.parse((await readFile(manifestPath)).toString("utf8"));
    const bootstrapValidators = await loadBootstrapSchemaValidators();
    if (!bootstrapValidators.validateProjectManifest(manifest)) throw new Error("invalid manifest");

    const capabilityDefinitions = await loadProjectCapabilityDefinitions(projectRoot);
    const requirements = manifest.capabilities.map((requirement) => {
      if (!resolveRequirements) return copyRequirement(requirement);
      const capability = resolveCapability(catalog, requirement.id);
      const configKeys = new Set(capability.configKeys ?? []);
      if (requirement.config && Object.keys(requirement.config).some((key) => !configKeys.has(key))) {
        throw new Error("unsupported capability configuration");
      }
      return copyRequirement(requirement);
    });

    return {
      stackVersion: manifest.stackVersion,
      requirements,
      taskIds: collectTaskIds(requirements),
      capabilityDefinitions
    };
  } catch (error) {
    const bootstrapFailure = mapBootstrapError(error);
    if (bootstrapFailure) throw bootstrapFailure;
    if (error instanceof CapabilityError) {
      if (["CAPABILITY_UNKNOWN", "SURFACE_UNKNOWN", "CAPABILITY_DEFINITIONS_MISSING", "CAPABILITY_DEFINITIONS_INVALID"].includes(error.code)) {
        throw error;
      }
      throw new CapabilityError("CAPABILITY_REQUIREMENT_INVALID");
    }
    throw new CapabilityError("CAPABILITY_REQUIREMENT_INVALID");
  }
}
