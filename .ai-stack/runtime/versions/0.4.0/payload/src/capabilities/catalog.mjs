import { readFile } from "node:fs/promises";
import path from "node:path";

import { CapabilityError } from "./errors.mjs";
import { CAPABILITY_ID_PATTERN } from "./constants.mjs";
import { loadProjectCapabilityDefinitions } from "./project-definitions.mjs";
import { resolvePrimitive, validatePrimitiveConfig, validateProjectSurface } from "./primitives.mjs";
import { loadCapabilityValidators } from "./schema.mjs";
import { definitionDigestForCapability, primitiveContractIdentity } from "./freshness.mjs";

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

function validateProjectTarget(target) {
  if (typeof target !== "string" || !/^[a-z][a-z0-9-]*$/.test(target)) {
    throw new CapabilityError("CAPABILITY_TARGET_INVALID");
  }
}

function mergeProjectCapability(definition, catalog, projectIds, metadata) {
  if (!definition || typeof definition !== "object" || Array.isArray(definition)) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  const definitionKeys = new Set(["id", "description", "surfaces", "checks"]);
  if (Object.keys(definition).some((key) => !definitionKeys.has(key))) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  if (!CAPABILITY_ID_PATTERN.test(definition.id) || !Array.isArray(definition.surfaces) || definition.surfaces.length === 0 || definition.surfaces.length > 6) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  if (definition.description !== undefined && (typeof definition.description !== "string" || definition.description.length === 0 || definition.description.length > 256)) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  if (catalog.capabilities.some((candidate) => candidate.id === definition.id)) {
    throw new CapabilityError("CAPABILITY_DEFINITION_COLLISION");
  }
  if (projectIds.has(definition.id)) {
    throw new CapabilityError("CAPABILITY_DEFINITION_COLLISION");
  }
  projectIds.add(definition.id);
  if (new Set(definition.surfaces).size !== definition.surfaces.length) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }
  for (const surface of definition.surfaces) validateProjectSurface(surface);
  if (!Array.isArray(definition.checks) || definition.checks.length === 0) {
    throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  }

  const checkIds = new Set();
  const checks = definition.checks.map((check) => {
    const checkKeys = new Set(["id", "primitive", "target", "config"]);
    if (!check || typeof check !== "object" || Array.isArray(check) || Object.keys(check).some((key) => !checkKeys.has(key))) {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
    if (!CAPABILITY_ID_PATTERN.test(check.id) || !CAPABILITY_ID_PATTERN.test(check.primitive) || checkIds.has(check.id)) {
      throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
    }
    checkIds.add(check.id);
    validateProjectTarget(check.target);
    const primitive = resolvePrimitive(catalog, check.primitive);
    const config = validatePrimitiveConfig(check.config, primitive);
    const normalized = {
      id: check.id,
      importance: primitive.importance,
      driver: primitive.driver,
      effect: primitive.effect,
      preflightAllowed: primitive.preflightAllowed,
      timeoutMs: primitive.timeoutMs,
      freshness: primitive.freshness,
      evidence: primitive.evidence,
      primitiveId: primitive.id,
      targetClass: primitive.targetClass,
      symbolicTarget: check.target,
      primitiveContractIdentity: primitiveContractIdentity(primitive),
    };
    if (config !== undefined) normalized.config = config;
    return normalized;
  });

  const degradedPolicies = new Set(definition.checks.map((check) => resolvePrimitive(catalog, check.primitive).degradedPolicyContribution));
  if (degradedPolicies.size !== 1) throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");
  const definitionDigest = definitionDigestForCapability({
    id: definition.id,
    surfaces: definition.surfaces,
    checks
  });
  for (const check of checks) check.definitionDigest = definitionDigest;
  return {
    id: definition.id,
    definitionDigest,
    origin: "project",
    surfaces: clone(definition.surfaces),
    checks,
    degradedPolicy: [...degradedPolicies][0],
    repairs: [],
    provenance: {
      origin: "project",
      reference: metadata.reference,
      fileDigest: metadata.fileDigest
    }
  };
}

export function mergeCapabilityCatalog({ catalog, projectDefinitions } = {}) {
  if (!catalog || typeof catalog !== "object" || !Array.isArray(catalog.capabilities)) {
    throw new CapabilityError("CAPABILITY_STATE_INVALID");
  }
  const projectInput = projectDefinitions ?? {
    reference: undefined,
    fileDigest: undefined,
    capabilities: []
  };
  if (!Array.isArray(projectInput.capabilities)) throw new CapabilityError("CAPABILITY_DEFINITIONS_INVALID");

  const reserved = new Set([
    ...catalog.capabilities.map((capability) => capability.id),
    ...(catalog.reservedCapabilityIds ?? [])
  ]);
  const projectIds = new Set();
  const coreCapabilities = catalog.capabilities.map((capability) => ({
    ...clone(capability),
    origin: "core",
    provenance: { origin: "core" }
  }));
  const projectCapabilities = projectInput.capabilities.map((definition) => {
    if (reserved.has(definition?.id)) throw new CapabilityError("CAPABILITY_DEFINITION_COLLISION");
    return mergeProjectCapability(
      definition,
      { ...catalog, capabilities: catalog.capabilities },
      projectIds,
      { reference: projectInput.reference, fileDigest: projectInput.fileDigest }
    );
  });
  return deepFreeze({
    ...clone(catalog),
    capabilities: [...coreCapabilities, ...projectCapabilities]
  });
}

export async function loadLogicalCapabilityCatalog({ payloadRoot, projectRoot, manifestInputs } = {}) {
  const core = await loadCapabilityCatalog({ payloadRoot });
  let projectDefinitions = manifestInputs?.capabilityDefinitions;
  if (projectDefinitions === undefined && projectRoot !== undefined) {
    projectDefinitions = await loadProjectCapabilityDefinitions(projectRoot);
  }
  return mergeCapabilityCatalog({ catalog: core, projectDefinitions });
}

export async function loadCapabilityCatalog({ payloadRoot }) {
  try {
    if (typeof payloadRoot !== "string" || payloadRoot.length === 0) throw new Error("payload root required");
    const catalogPath = path.join(payloadRoot, "runtime", "capabilities", "catalog.json");
    const catalog = JSON.parse((await readFile(catalogPath)).toString("utf8"));
    const validators = await loadCapabilityValidators();
    if (!validators.validateCapabilityCatalog(catalog)) throw new Error("invalid catalog");
    return deepFreeze(clone(catalog));
  } catch (error) {
    if (error instanceof CapabilityError) throw error;
    throw new CapabilityError("CAPABILITY_STATE_INVALID");
  }
}

export function resolveCapability(catalog, id, surface) {
  const capability = catalog?.capabilities?.find((candidate) => candidate.id === id);
  if (!capability) throw new CapabilityError("CAPABILITY_UNKNOWN");
  if (surface !== undefined && !capability.surfaces.includes(surface)) {
    throw new CapabilityError("SURFACE_UNKNOWN");
  }
  return deepFreeze(clone(capability));
}
