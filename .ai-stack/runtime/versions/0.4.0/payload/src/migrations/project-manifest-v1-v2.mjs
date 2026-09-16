import path from "node:path";

import { bootstrapError } from "../bootstrap/errors.mjs";
import {
  loadBootstrapSchemaValidators,
  validateProjectManifestTaskReferences
} from "../bootstrap/schema.mjs";

function invalidManifest() {
  throw bootstrapError("INVALID_MANIFEST");
}

function clone(value) {
  try {
    return structuredClone(value);
  } catch {
    invalidManifest();
  }
}

function canonicalTaskIds(values) {
  try {
    return [...new Set(values)].sort();
  } catch {
    invalidManifest();
  }
}

function assertDistinctOutput(sourcePath, outputPath) {
  if (sourcePath === undefined && outputPath === undefined) return;
  if (typeof sourcePath !== "string" || typeof outputPath !== "string") invalidManifest();
  try {
    if (path.resolve(sourcePath) === path.resolve(outputPath)) invalidManifest();
  } catch {
    invalidManifest();
  }
}

function deriveLegacyTaskIds(legacyManifest) {
  const taskIds = [];
  for (const requirement of legacyManifest.capabilities) {
    if (requirement.activation === "always") continue;
    taskIds.push(...requirement.activation.tasks);
  }
  return canonicalTaskIds(taskIds);
}

/**
 * Build a reviewable v2 manifest candidate from a validated v1 manifest.
 * This function is intentionally pure: it never reads or writes a project file.
 */
export async function migrateProjectManifestV1ToV2({
  legacyManifest,
  approvedAdditionalTasks = [],
  sourcePath,
  outputPath
} = {}) {
  if (!legacyManifest || typeof legacyManifest !== "object" || Array.isArray(legacyManifest)) {
    invalidManifest();
  }
  if (!Array.isArray(approvedAdditionalTasks)) invalidManifest();
  assertDistinctOutput(sourcePath, outputPath);

  const validators = await loadBootstrapSchemaValidators();
  const source = clone(legacyManifest);
  if (!validators.validateProjectManifestV1(source)) invalidManifest();

  const derivedLegacyTaskIds = deriveLegacyTaskIds(source);
  const approvedAdditionalTaskIds = canonicalTaskIds(approvedAdditionalTasks);
  const taskIds = canonicalTaskIds([...derivedLegacyTaskIds, ...approvedAdditionalTaskIds]);
  const candidate = {
    ...source,
    schemaVersion: 2,
    tasks: taskIds
  };

  if (!validators.validateProjectManifest(candidate)) invalidManifest();
  if (!validateProjectManifestTaskReferences(candidate)) invalidManifest();

  return {
    candidate,
    evidence: {
      sourceSchemaVersion: source.schemaVersion,
      candidateSchemaVersion: candidate.schemaVersion,
      derivedLegacyTaskIds,
      approvedAdditionalTaskIds,
      taskIds,
      validation: {
        schema: "pass",
        taskReferences: "pass"
      }
    }
  };
}
